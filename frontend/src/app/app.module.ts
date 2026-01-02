import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

// Components
import { LoginComponent } from './auth/login/login.component';
import { SignupComponent } from './auth/signup/signup.component';
import { ChatbotComponent } from './components/chatbot/chatbot.component';
import { NavbarComponent } from './components/navbar/navbar.component';
import { ChatHistoryComponent } from './components/chat-history/chat-history.component'; // ✅ Add this

// Services & Guards
import { AuthGuard } from './shared/auth.guard';
import { AuthService } from './shared/auth.service';
import { ChatService } from './shared/chat.service';

// Interceptor
import { AuthInterceptor } from './auth/interceptors/auth.interceptor';
import { LoginSuccessComponent } from './auth/login-success/login-success.component';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    SignupComponent,
    ChatbotComponent,
    NavbarComponent,
    ChatHistoryComponent,
    LoginSuccessComponent  // ✅ Add this
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [
    AuthService,
    ChatService,
    AuthGuard,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
