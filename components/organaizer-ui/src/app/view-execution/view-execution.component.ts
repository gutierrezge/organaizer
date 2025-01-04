import { Component, OnDestroy, OnInit } from '@angular/core';
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
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { ImageDialogComponent } from '../image-dialog/image-dialog.component';


@Component({
  selector: 'app-view-execution',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatButtonModule, MatDialogModule,
    MatProgressSpinnerModule, MatFormFieldModule, MatIconModule, MatTooltipModule],
  templateUrl: './view-execution.component.html',
  styleUrl: './view-execution.component.css'
})
export class ViewExecutionComponent implements OnInit, OnDestroy{

  private POLL_INTERVAL_SECONDS:number = 5;
  executionId:string = '';
  execution?:Execution;
  private intervalSubscription?: Subscription;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private organaizerService: OrganaizerService,
    private dialog: MatDialog
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

  ngOnDestroy() {
    this.intervalSubscription?.unsubscribe();
  }

  openImageDialog(imageUrl: string): void {
    this.dialog.open(ImageDialogComponent, {
      data: { imageUrl },
      maxWidth: '90vw',
      maxHeight: '90vh',
      panelClass: ['image-dialog'],
      hasBackdrop: true
    });
  }

  redo():void {
    if (this.execution) {
      this.organaizerService.redo(this.execution).subscribe({
        error: (error) => {
          alert(error);
        }
      });
      this.execution = undefined;
    }
  }

  deleteExecution():void {
    if (this.execution) {
      if (confirm("Are you sure you want to delete execution " + this.execution.id)) {
        this.organaizerService.deleteExecution(this.execution).subscribe({
          next: () => {
            this.router.navigate(['/'])
          },
          error: (error) => {
            alert(error);
          }
        });
        this.execution = undefined;
      }
    }
  }

  private loadData() {
    this.execution = undefined;
    this.organaizerService.findById(this.executionId).subscribe({
      next: (e:Execution) => {
        this.execution = e;
      },
      error: (error) => {
        alert(error);
      }
    });
  }
}
