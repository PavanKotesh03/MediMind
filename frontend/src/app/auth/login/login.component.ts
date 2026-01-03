import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from 'src/app/shared/auth.service';
import { ChatService } from 'src/app/shared/chat.service';

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

    console.log('Attempting login:', this.email);

    this.authService.login(this.email, this.password).subscribe({
      next: (response) => {
        console.log('Login successful:', response);
        this.isLoading = false;

        if (response.success) {
          console.log('Token stored in cache');
          console.log('Token stored in cache');
          this.router.navigate(['/chat']);
        } else {
          this.errorMessage = response.message || 'Login failed';
        }
      },
      error: (error) => {
        console.error('Login error:', error);
        this.isLoading = false;

        if (error.status === 401) {
          this.errorMessage = 'Invalid email or password';
        } else if (error.status === 0) {
          this.errorMessage = 'Cannot connect to server. Is the backend running?';
        } else {
          this.errorMessage = error.error?.detail || 'Login failed. Please try again.';
        }
      }
    });
  }


}
