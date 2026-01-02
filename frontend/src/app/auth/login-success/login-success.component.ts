import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../shared/auth.service';

@Component({
  selector: 'app-login-success',
  template: `
    <div style="display: flex; justify-content: center; align-items: center; height: 100vh; flex-direction: column;">
      <h2>Logging you in...</h2>
      <p>Please wait while we redirect you.</p>
    </div>
  `,
  styles: []
})
export class LoginSuccessComponent implements OnInit {

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService
  ) { }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      const token = params['token'];
      const error = params['error'];

      if (token) {
        console.log('OAuth login successful, token received');
        this.authService.setToken(token);

        // Build user data from token (basic decoding) or fetch profile
        // For now, we just redirect. The token is enough for API calls.
        // We can manually decode the token payload if needed to get the email immediately.
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          const userData = { email: payload.sub };
          this.authService.setUserData(userData);
        } catch (e) {
          console.error('Failed to decode token', e);
        }

        this.router.navigate(['/chat']);
      } else if (error) {
        console.error('OAuth error:', error);
        this.router.navigate(['/login'], { queryParams: { error: 'oauth_failed' } });
      } else {
        this.router.navigate(['/login']);
      }
    });
  }
}
