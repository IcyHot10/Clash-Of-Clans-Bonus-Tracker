import { Component } from '@angular/core';
import { HeaderComponent } from "./header/header.component";
import { LeaderboardComponent } from "./leaderboard/leaderboard.component";
import { DUMMY_CLAN } from "./dummy_clan";

@Component({
  selector: 'app-root',
  imports: [HeaderComponent, LeaderboardComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'Clash of Clans Bonus Tracker';
  clan = {};

  onClanTagSelected(clanTag: string) {
    console.log(clanTag);
    this.clan = clanTag === DUMMY_CLAN.clanTag ? DUMMY_CLAN : {};
  }
}
