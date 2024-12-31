import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { OrganaizerService } from '../service/service';
import { Execution } from '../models/models';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-view-execution',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatTooltipModule],
  templateUrl: './view-execution.component.html',
  styleUrl: './view-execution.component.css'
})
export class ViewExecutionComponent {

  execution?:Execution;
  constructor(
    private route: ActivatedRoute,
    private organaizerService: OrganaizerService
  ) {}

  ngOnInit() {
    this.route.params.subscribe(params => {
      console.log(params)
      if (params && params['id']) {
        this.loadData(params['id']);
      }
    });
  }

  private loadData(id: string) {
    this.organaizerService.findById(id).subscribe(e => {
      this.execution = e;
      console.log(this.execution);
    });
  }
}
