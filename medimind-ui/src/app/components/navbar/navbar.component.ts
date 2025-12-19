import { Component, Input } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/auth.service';
import { ChatService } from '../../shared/chat.service';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent {
  @Input() userName!: string;
  menuOpen = false;

  constructor(
    private router: Router,
    private authService: AuthService,
    private chatService: ChatService
  ) {}

  toggleMenu() {
    this.menuOpen = !this.menuOpen;
  }

  newChat() {
    this.menuOpen = false;
    this.chatService.resetChat();
  }

  logout() {
    this.menuOpen = false;
    this.authService.clearUser();
    this.router.navigate(['/login']);
  }
}
