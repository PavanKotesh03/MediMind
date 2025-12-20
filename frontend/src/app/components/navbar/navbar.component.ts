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
          this.chatService.clearSession();
        },
        error: () => {
          this.chatService.clearSession();
        }
      });
    } else {
      // Just trigger reset
      this.chatService.clearSession();
    }
    
    this.menuOpen = false;
    
    // Navigate to chatbot if not already there
    if (this.router.url !== '/chatbot') {
      this.router.navigate(['/chatbot']);
    }
  }

  logout() {
    this.authService.clearUser();
    this.chatService.clearSession();
    this.router.navigate(['/login']);
    this.menuOpen = false;
  }
}
