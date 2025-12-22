import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): boolean {
    const userName = localStorage.getItem('userName');

    if (userName) {
      return true; //  allow access
    }

    //  block access
    this.router.navigate(['/login']);
    return false;
  }
}
