import { Component, OnInit } from '@angular/core';
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
export class ExecutionListComponent implements OnInit {

  isLoading: boolean = false;
  displayedColumns: string[] = ['id', 'container', 'boxes', 'volume', 'status', 'created', 'actions'];
  executions = new MatTableDataSource<Execution>();

  constructor(private router: Router, private organaizerService: OrganaizerService) {}
  
  ngOnInit(): void {
    this.loadExecutions()
  }

  loadExecutions(): void {
    this.isLoading = true;
    this.organaizerService.findAll().subscribe({
      next: (executions:Executions) => {
        this.executions = new MatTableDataSource<Execution>(executions.executions);
      },
      error: (error) => {
        this.isLoading = false
        alert(error);
      },
      complete: () => this.isLoading = false
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
    this.executions.filter = filterValue.trim().toLowerCase();
  }

}
