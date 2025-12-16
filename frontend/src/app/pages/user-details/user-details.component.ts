import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-user-details',
  templateUrl: './user-details.component.html',
  styleUrls: ['./user-details.component.scss']
})
export class UserDetailsComponent {

  details: any = {};

  constructor(private auth: AuthService, private router: Router) {}

  submit() {
    this.auth.saveDetails(this.details);
    this.router.navigate(['/chat']);
  }
}
