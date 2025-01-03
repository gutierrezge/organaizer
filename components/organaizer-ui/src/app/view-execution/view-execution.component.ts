import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { OrganaizerService } from '../service/service';
import { Execution } from '../models/models';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-view-execution',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatButtonModule,
    MatProgressSpinnerModule, MatFormFieldModule, MatIconModule, MatTooltipModule],
  templateUrl: './view-execution.component.html',
  styleUrl: './view-execution.component.css'
})
export class ViewExecutionComponent {

  private POLL_INTERVAL_SECONDS:number = 5;
  executionId:string = '';
  execution?:Execution;
  isLoading: boolean = false;
  private intervalSubscription?: Subscription;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private organaizerService: OrganaizerService
  ) {}

  ngOnInit() {
    this.route.params.subscribe(params => {
      console.log(params)
      if (params && params['id']) {
        this.executionId = params['id'];
      }
    });
    this.intervalSubscription = interval(this.POLL_INTERVAL_SECONDS * 1000).subscribe(() => {
      if (!this.execution && this.executionId !== '') {
        this.loadData();
      }
    });
  }

  redo():void {
    if (this.execution) {
      this.isLoading = true;
      this.organaizerService.redo(this.execution).subscribe({
        next: (execution:Execution) => {
          this.loadData();
        },
        error: (error) => {
          this.isLoading = false
          alert(error);
        },
        complete: () => this.isLoading = false
      });
    }
  }

  deleteExecution():void {
    if (this.execution) {
      if (confirm("Are you sure you want to delete execution " + this.execution.id)) {
        this.isLoading = true;
        this.organaizerService.deleteExecution(this.execution).subscribe({
          next: () => {
            this.router.navigate(['/'])
          },
          error: (error) => {
            this.isLoading = false
            alert(error);
          },
          complete: () => this.isLoading = false
        });
      }
    }
  }

  private loadData() {
    this.isLoading = true;
    this.organaizerService.findById(this.executionId).subscribe({
      next: (e:Execution) => {
        this.execution = e;
      },
      error: (error) => {
        this.isLoading = false
        alert(error);
      },
      complete: () => this.isLoading = false
    });
  }
}
