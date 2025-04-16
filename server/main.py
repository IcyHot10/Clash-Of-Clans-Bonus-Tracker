from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import asyncio

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
CLAN_TAG = "%232LPOGLU2U"  # URL encoded clan tag


async def get_league(clan_tag: str) -> List[Dict[str, Any]]:
    """Get the current league information and process wars."""
    rankings: List[Dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/clans/{clan_tag}/currentwar/leaguegroup",
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
            url = f"{BASE_URL}/clans/{clan_tag}/currentwar/leaguegroup"
            data = response.json()
            
            if data.get("state") in ["inWar", "ended"]:
                summ_clan = await find_wars(data.get("rounds", []))
                rankings = consolidate_leaderboard(summ_clan)
                return rankings
            else:
                return
        except Exception as e:
            print(f"Error getting league: {e}")

async def get_war(war_tag: str) -> List[Dict[str, Any]]:
    """Get war information and process member data."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/clanwarleagues/wars/{war_tag.replace('#', '%23')}",
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
            data = response.json()
            
            if data["clan"]["name"] == "Tranquility":
                clan = data["clan"]["members"]
                opps = data["opponent"]["members"]
            elif data["opponent"]["name"] == "Tranquility":
                clan = data["opponent"]["members"]
                opps = data["clan"]["members"]
            else:
                return
            
            summ_opps = [
                {"tag": opp["tag"], "th": opp["townhallLevel"], "pos": opp["mapPosition"]}
                for opp in opps
            ]
            
            summ_clan = []
            for member in clan:
                stars = 0
                perc = 0
                opp_tag = ""
                
                if member.get("attacks"):
                    opp_tag = member["attacks"][0]["defenderTag"]
                    opp = next((o for o in summ_opps if o["tag"] == opp_tag), None)
                    
                    if opp:
                        higher_th_opps = [o for o in summ_opps if o["pos"] < opp["pos"] and o["th"] < opp["th"]]
                        opp_th = min(higher_th_opps, key=lambda x: x["th"])["th"] if higher_th_opps else opp["th"]
                        
                        stars = member["attacks"][0]["stars"]
                        if member["townhallLevel"] < opp_th and stars != 0:
                            stars += (opp_th - member["townhallLevel"])
                        perc = member["attacks"][0]["destructionPercentage"]
                
                summ_clan.append({
                    "tag": member["tag"],
                    "name": member["name"],
                    "th": member["townhallLevel"],
                    "opp": opp_tag,
                    "stars": stars,
                    "percentage": perc
                })
            
            return summ_clan
        except Exception as e:
            print(f"Error getting war: {e}")

async def find_wars(rounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process all wars in the given rounds."""
    summ_clan = []
    for round_data in rounds:
        for war_tag in round_data.get("warTags", []):
            if war_tag != "#0":
                summ_clan = summ_clan.extend(await get_war(war_tag))
    return summ_clan

async def consolidate_leaderboard(summ_clan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Consolidate leaderboard entries and sort them."""
    
    for sum_data in summ_clan:
        if not rankings:
            rankings.append({
                "tag": sum_data["tag"],
                "name": sum_data["name"],
                "stars": sum_data["stars"],
                "percentage": sum_data["percentage"]
            })
        else:
            index = next((i for i, r in enumerate(rankings) if r["tag"] == sum_data["tag"]), -1)
            if index == -1:
                rankings.append({
                    "tag": sum_data["tag"],
                    "name": sum_data["name"],
                    "stars": sum_data["stars"],
                    "percentage": sum_data["percentage"]
                })
            else:
                rankings[index]["stars"] += sum_data["stars"]
                rankings[index]["percentage"] += sum_data["percentage"]
    
    # Sort rankings
    rankings.sort(key=lambda x: (-x["stars"], -x["percentage"]))
    return rankings

@app.get("/")
async def read_root():
    return {"message": "Welcome to Clash of Clans Bonus Tracker API"}

@app.get("/leaderboard")
async def get_leaderboard():
    """Get the current leaderboard."""
    return rankings

@app.post("/refresh")
async def refresh_leaderboard():
    """Refresh the leaderboard data."""
    global rankings
    rankings = []
    await get_league()
    return {"message": "Leaderboard refreshed successfully"}

if __name__ == "__main__":
    asyncio.run(get_league(CLAN_TAG))


