import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  email = '';
  password = '';
  errorMessage = '';

  constructor(
    private router: Router,
    private authService: AuthService
  ) {
    if (localStorage.getItem('userName')) {
      this.router.navigate(['/chat']);
    }
  }




  login() {
    this.errorMessage = '';

    if (!this.email || !this.password) {
      this.errorMessage = 'Please enter email and password';
      return;
    }

    const nameFromEmail = this.email.split('@')[0];

    // 🔥 FIX: reactive update
    this.authService.setUserName(nameFromEmail);

    this.router.navigate(['/chat']);
  }
}
