import { CommonModule } from '@angular/common';
import { AfterViewInit, Component } from '@angular/core';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NavbarComponent } from '../navbar/navbar.component';
import { Router, RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { OrganaizerService } from '../service/service';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';
import { CreateExecutionRequest, PresignedUrlResponse } from '../models/models';

@Component({
  selector: 'app-new-execution',
  standalone: true,
  imports: [NavbarComponent, RouterModule, CommonModule, MatProgressSpinnerModule,
      MatFormFieldModule, MatInputModule, FormsModule,
      MatIconModule, MatButtonModule, MatTooltipModule],
  templateUrl: './new-execution.component.html',
  styleUrl: './new-execution.component.css'
})
export class NewExecutionComponent implements AfterViewInit {
  isLoading: boolean = false;
  containerWidth?:number;
  containerHeight?:number;
  containerDepth?:number;
  selectedFile?:File
  error:boolean = false;
  hasAllData = false;
  
  constructor(private router: Router, private organaizerService: OrganaizerService) {}

  ngAfterViewInit(): void {
    this.containerWidth = undefined;
    this.containerHeight = undefined;
    this.containerDepth = undefined;
    this.selectedFile = undefined;
  }

  newExecution(): void {
    this.error = false;
    if (this.containerWidth && this.containerHeight && this.containerDepth && this.selectedFile) {
      this.isLoading = true;
      const fileToUpload:File = this.selectedFile;
      const w = this.containerWidth;
      const h = this.containerHeight;
      const d = this.containerDepth;
      this.organaizerService.presignedUrls(fileToUpload.name).subscribe({
        next: (url:PresignedUrlResponse) => {
          const execution:CreateExecutionRequest = {
            id: url.id,
            key: url.key,
            container_width: w,
            container_height: h,
            container_depth: d
          }
          this.organaizerService.uploadFile(url.url, fileToUpload).subscribe({
            next: () => {
              this.organaizerService.createExecution(execution).subscribe({
                next:() => {
                  this.router.navigate(['/'])
                },
                error: (error) => {
                  this.isLoading = false
                  alert(error);
                },
                complete: () => this.isLoading = false
              });
            },
            error: (error) => {
              this.isLoading = false
              alert(error);
            },
            complete: () => this.isLoading = false
          });
          
        },
        error: (error) => {
          this.isLoading = false
          alert(error);
        },
        complete: () => this.isLoading = false
      });
    } else {
      this.error = true
    }
  }

  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0];
  }


  isNumber(event: KeyboardEvent): void {
    const pattern = /^[0-9.]$/;
    const inputChar = event.key;
    const inputElement = event.target as HTMLInputElement;
    const value = inputElement.value;
    
    if (event.key === 'Backspace' || event.key === 'Delete' || 
        event.key === 'ArrowLeft' || event.key === 'ArrowRight' ||
        event.key === 'Tab') {
      return;
    }
  
    if (inputChar === '.' && value.includes('.')) {
      event.preventDefault();
      return;
    }
  
    if (value.includes('.') && value.split(".")[1].length > 1) {
        event.preventDefault();
        return;
    }
  
    if (!pattern.test(inputChar)) {
      event.preventDefault();
    }
  }
  
  isDecimal(value: string | number): boolean {
    if (value === null || value === undefined || value === '') {
      return false;
    }
    
    const number = typeof value === 'string' ? parseFloat(value) : value;
    const decimalPlaces = number.toString().split('.')[1]?.length || 0;
    
    return !isNaN(number) && decimalPlaces <= 2;
  }
}
