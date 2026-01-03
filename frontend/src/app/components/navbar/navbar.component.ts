import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from 'src/app/shared/auth.service';
import { ChatService } from 'src/app/shared/chat.service';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit {
  userName = '';
  menuOpen = false;

  constructor(
    private router: Router,
    private authService: AuthService,
    private chatService: ChatService
  ) { }

  ngOnInit() {
    this.authService.userData$.subscribe(userData => {
      if (userData) {
        // Extract first name
        const fullName = userData.name || userData.email || 'User';
        this.userName = fullName.split(' ')[0];
      }
    });
  }

  toggleMenu() {
    this.menuOpen = !this.menuOpen;
  }

  toggleSidebar() {
    this.chatService.toggleSidebar();
  }

  newChat() {
    const sessionId = this.chatService.getSessionId();

    if (sessionId) {
      this.chatService.resetChat(sessionId).subscribe({
        next: () => {
          console.log('Chat reset successful');
          this.chatService.clearSession();
        },
        error: (err) => {
          console.error('Reset API failed:', err);
          // Clear anyway
          this.chatService.clearSession();
        }
      });
    } else {
      this.chatService.clearSession();
    }

    this.menuOpen = false;
  }

  logout() {
    this.authService.clearUser();
    this.chatService.clearSession();
    this.router.navigate(['/login']);
    this.menuOpen = false;
  }
}
