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
        this.userName = userData.name || userData.email || 'User';
      }
    });
  }

  toggleMenu() {
    this.menuOpen = !this.menuOpen;
  }

  newChat() {
    console.log('NAVBAR: New Chat clicked');
    
    // Clear current session
    this.chatService.clearSession();
    
    // Call /start API to create new session
    this.chatService.startInterview('').subscribe({
      next: (res: any) => {
        console.log('NAVBAR: Start API response:', res);
        
        const newSessionId = res.data?.session_id;
        
        if (newSessionId) {
          console.log('NAVBAR: New session created:', newSessionId);
          this.chatService.setSessionId(newSessionId);
          
          // Navigate WITHOUT reloading - component will handle it
          this.router.navigate(['/chat', newSessionId], { 
            replaceUrl: true,
            skipLocationChange: false
          });
        } else {
          console.error('NAVBAR: No session_id in response');
          alert('Failed to create new chat session');
        }
      },
      error: (err) => {
        console.error('NAVBAR: Failed to create session:', err);
        alert('Failed to start new chat. Please try again.');
      }
    });

    this.menuOpen = false;
  }

  logout() {
    this.authService.logout();
    this.chatService.clearSession();
    this.router.navigate(['/login']);
    this.menuOpen = false;
  }
}
