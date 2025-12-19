import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd, Event as RouterEvent } from '@angular/router';
import { AuthService } from './shared/auth.service';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  userName = '';
  showNavbar = false;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    // Listen to login/logout changes
    this.authService.userName$.subscribe(name => {
      this.userName = name;
    });

    // Show navbar ONLY on non-auth routes
    this.router.events
      .pipe(
        filter(
          (event: RouterEvent): event is NavigationEnd =>
            event instanceof NavigationEnd
        )
      )
      .subscribe(event => {
        const authRoutes = ['/login', '/signup'];
        this.showNavbar = !authRoutes.includes(event.urlAfterRedirects);
      });
  }
}
