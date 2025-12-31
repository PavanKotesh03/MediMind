import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/auth.service';
import { ChatService } from '../../shared/chat.service';
 
 
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
  ) {}
 
 
  ngOnInit() {
    this.authService.userData$.subscribe(userData => {
      if (userData) {
        this.userName = userData.name;
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
          console.log('Chat reset successful');
          // Clear session triggers observable
          this.chatService.clearSession();
        },
        error: (err) => {
          console.error('Reset API failed:', err);
          // Still clear on frontend even if backend fails
          this.chatService.clearSession();
        }
      });
    } else {
      // No active session, just trigger UI reset
      this.chatService.clearSession();
    }
    this.menuOpen = false;
    // NO NAVIGATION - Observable pattern handles the reset
  }
 
 
  logout() {
    this.authService.clearUser();
    this.chatService.clearSession();
    this.router.navigate(['/login']);
    this.menuOpen = false;
  }
}