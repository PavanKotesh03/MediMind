import { Component, OnInit, Input } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/auth.service';
import { ChatService } from '../../shared/chat.service';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit {
  @Input() userName = '';
  menuOpen = false;

  constructor(
    private router: Router,
    private authService: AuthService,
    private chatService: ChatService
  ) {}

  ngOnInit() {
    // Subscribe to userData to get actual name from backend
    this.authService.userData$.subscribe(userData => {
      if (userData) {
        this.userName = userData.name; // Real name from backend
      }
    });
  }

  toggleMenu() {
    this.menuOpen = !this.menuOpen;
  }

  newChat() {
    const sessionId = this.chatService.getSessionId();
    
    if (sessionId) {
      // Call backend reset API
      this.chatService.resetChat(sessionId).subscribe({
        next: () => {
          // Clear session and trigger UI reset
          this.chatService.clearSession();
        },
        error: () => {
          // Still clear locally even if backend fails
          this.chatService.clearSession();
        }
      });
    } else {
      // No active session, just trigger UI reset
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
