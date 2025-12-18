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
  showNavbar = true;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    // React to login/logout immediately
    this.authService.userName$.subscribe(name => {
      this.userName = name;
    });

    // React to route changes (HIDE navbar on auth pages)
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
