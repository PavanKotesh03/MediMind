import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {

  email = '';
  password = '';

  constructor(private auth: AuthService, private router: Router) {}

  login() {
    const success = this.auth.login(this.email, this.password);

    if (!success) {
      alert('Invalid credentials');
      return;
    }

    const user = this.auth.getLoggedInUser();

    // ✅ Skip details if already filled
    if (user?.name && user?.age && user?.gender) {
      this.router.navigate(['/chat']);
    } else {
      this.router.navigate(['/details']);
    }
  }
}
