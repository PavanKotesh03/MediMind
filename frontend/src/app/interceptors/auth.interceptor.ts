import { Injectable } from '@angular/core';
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    console.log('INTERCEPTOR HIT - URL:', req.url);
    
    const token = localStorage.getItem('access_token');
    console.log('Token exists:', !!token);
    
    if (token) {
      const cloned = req.clone({
        headers: req.headers.set('Authorization', `Bearer ${token}`)
      });
      
      console.log('Authorization header added');
      return next.handle(cloned);
    }
    
    console.log('No token - passing unchanged');
    return next.handle(req);
  }
}
