import {
  Component,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss'],
})
export class NavbarComponent {
  isNavbarCollapsed = true;

  links = [
    {
      title: "Home",
      fragment: ""
    },
    {
      title: "Projects",
      fragment: "projects"
    },
    {
      title: "Articles",
      dropdown: [
        {
          title: "Recent articles",
          fragment: "recent-articles"
        },
        {
          title: "Hardware",
          fragment: "hardware"
        },
        {
          title: "AI",
          fragment: "ai"
        }
      ]
    }
  ];

  constructor(public route: ActivatedRoute) { }

}
