import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {

  chatStarted = false;
  firstBotMessage = '';
  sessionId = '';
  userName = '';


  // ⬇️ NOW ACCEPTS OBJECT (not string)
  onUserSubmitted(event: { sessionId: string; firstMessage: string }) {
  this.chatStarted = true;              // 👈 switch UI immediately
  this.sessionId = event.sessionId;
  this.firstBotMessage = event.firstMessage;
}

}
