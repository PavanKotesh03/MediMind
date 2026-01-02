import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/auth.service';
import { ChatService } from '../../shared/chat.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  email: string = '';
  password: string = '';
  errorMessage: string = '';
  isLoading: boolean = false;

  constructor(
    private router: Router,
    private authService: AuthService,
    private chatService: ChatService
  ) {
    if (this.authService.isLoggedIn()) {
      this.router.navigate(['/chat']);
    }
  }

  login() {
    this.errorMessage = '';
    this.isLoading = true;

    if (!this.email || !this.password) {
      this.errorMessage = 'Please enter email and password';
      this.isLoading = false;
      return;
    }

    console.log('LOGIN: Attempting login:', this.email);

    this.authService.login(this.email, this.password).subscribe({
      next: (response) => {
        console.log('LOGIN: Login successful');
        this.isLoading = false;
        
        if (response.success) {
          console.log('LOGIN: Token stored, navigating immediately');
          this.router.navigate(['/chat']);
          
          // Call /start to create empty session
          console.log('LOGIN: Creating empty session with /start');
          this.chatService.startInterview('').subscribe({
            next: (res: any) => {
              const sessionId = res.data?.session_id;
              
              if (sessionId) {
                console.log('LOGIN: Empty session created:', sessionId);
                this.chatService.setSessionId(sessionId);
                this.router.navigate(['/chat', sessionId], { replaceUrl: true });
              }
            },
            error: (error) => {
              console.error('LOGIN: Session creation failed:', error);
            }
          });
        } else {
          this.errorMessage = response.message || 'Login failed';
        }
      },
      error: (error) => {
        console.error('LOGIN: Login error:', error);
        this.isLoading = false;
        
        if (error.status === 401) {
          this.errorMessage = 'Invalid email or password';
        } else if (error.status === 0) {
          this.errorMessage = 'Cannot connect to server';
        } else {
          this.errorMessage = error.error?.detail || 'Login failed';
        }
      }
    });
  }
}
