import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.scss']
})
export class SignupComponent {

  data: any = {};

  constructor(private auth: AuthService, private router: Router) {}

  submit() {
    if (this.data.password !== this.data.confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    this.auth.signup(this.data);
    this.router.navigate(['/login']);
  }
}
