import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/auth.service';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.css']
})
export class SignupComponent {
  name = '';
  age!: number;
  gender = '';
  email = '';
  password = '';
  confirmPassword = '';
  errorMessage = '';

  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  isValidName(name: string): boolean {
    return /^[A-Za-z ]+$/.test(name.trim());
  }

  signup() {
    this.errorMessage = '';

    if (!this.name || !this.isValidName(this.name)) {
      this.errorMessage = 'Please enter a valid name (letters only)';
      return;
    }

    if (!this.age || this.age <= 0 || this.age >= 100) {
      this.errorMessage = 'Please enter a valid age below 100';
      return;
    }

    if (!this.gender) {
      this.errorMessage = 'Please select a gender';
      return;
    }

    if (!this.email) {
      this.errorMessage = 'Please enter a valid email';
      return;
    }

    if (!this.password || this.password.length < 6) {
      this.errorMessage = 'Password must be at least 6 characters';
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match';
      return;
    }

    // 🔥 FIX: reactive update
    this.authService.setUserName(this.name.trim());

    this.router.navigate(['/chat']);
  }
}
