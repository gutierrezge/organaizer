import { Component, OnDestroy, OnInit } from '@angular/core';
import { NavbarComponent } from '../navbar/navbar.component';
import { CommonModule } from '@angular/common';
import { OrganaizerService } from '../service/service';
import { Execution, Executions } from '../models/models';
import { Router, RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatTableDataSource, MatTableModule} from '@angular/material/table';
import { MatFormFieldModule} from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { interval, Subscription } from 'rxjs';


@Component({
  selector: 'app-execution-list',
  standalone: true,
  imports: [
    NavbarComponent, RouterModule, CommonModule, MatProgressSpinnerModule,
    MatTableModule, MatFormFieldModule, MatInputModule,
    MatIconModule, MatButtonModule, MatTooltipModule
  ],
  templateUrl: './execution-list.component.html',
  styleUrl: './execution-list.component.css'
})
export class ExecutionListComponent implements OnInit, OnDestroy {

  private POLL_INTERVAL_SECONDS:number = 5;
  private intervalSubscription?: Subscription
  isLoading: boolean = false;
  displayedColumns: string[] = ['id', 'container', 'boxes', 'volume', 'status', 'created', 'actions'];
  datasource = new MatTableDataSource<Execution>();
  executions?: Execution[];

  constructor(private router: Router, private organaizerService: OrganaizerService) {}
  
  ngOnInit(): void {
    this.loadExecutions();
    this.intervalSubscription = interval(this.POLL_INTERVAL_SECONDS * 1000).subscribe(() => {
      this.loadExecutions();
    });
  }

  loadExecutions(): void {
    this.isLoading = true;
    this.organaizerService.findAll().subscribe({
      next: (executions:Executions) => {
        if (this.hasDataChanged(executions.executions)) {
          this.datasource = new MatTableDataSource<Execution>(executions.executions);
          this.executions = executions.executions
        }
      },
      error: (error) => {
        this.isLoading = false
        alert(error);
      },
      complete: () => this.isLoading = false
    });
  }

  private hasDataChanged(new_executions:Execution[]): boolean {
    return JSON.stringify(this.executions) != JSON.stringify(new_executions)
  }

  redo(execution:Execution):void {
    this.organaizerService.redo(execution).subscribe({
      next: (execution:Execution) => {
      },
      error: (error) => {
        this.isLoading = false
        alert(error);
      },
      complete: () => this.loadExecutions()
    });
  }

  deleteExecution(execution:Execution):void {
    if (confirm("Are you sure you want to delete execution " + execution.id)) {
      this.isLoading = true;
      this.organaizerService.deleteExecution(execution).subscribe({
        next: (execution:Execution) => {
        },
        error: (error) => {
          this.isLoading = false
          alert(error);
        },
        complete: () => this.loadExecutions()
      });
    }
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.datasource.filter = filterValue.trim().toLowerCase();
  }

  ngOnDestroy() {
    this.intervalSubscription?.unsubscribe();
  }

}
