import { Component } from '@angular/core';
import { ChatService } from '../../services/chat.service';
import { AuthService } from '../../services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent {

  message = '';
  user = this.auth.getLoggedInUser();
  messages = this.chat.getMessages(this.user?.email || '');

  constructor(
    private chat: ChatService,
    private auth: AuthService,
    private router: Router
  ) {}

  send() {
    if (!this.message || !this.user) return;

    this.chat.sendMessage(this.user.email, this.message);
    this.message = '';
    this.messages = this.chat.getMessages(this.user.email);
  }

  clear() {
    if (!this.user) return;
    this.chat.clear(this.user.email);
    this.messages = [];
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
