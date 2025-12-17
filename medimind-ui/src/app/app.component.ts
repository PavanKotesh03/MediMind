import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  userName: string = '';
  chatStarted = false

  onUserSubmitted(name: string) {
    this.userName = name;
    this.chatStarted = true;
  }
}
