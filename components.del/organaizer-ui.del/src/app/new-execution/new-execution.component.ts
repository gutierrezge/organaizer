import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, ElementRef, ViewChild } from '@angular/core';
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
import { CreateExecutionRequest, SelectedFile, UploadImagesResponse } from '../models/models';
import { v4 as uuidv4 } from 'uuid';
import { forkJoin, Observable } from 'rxjs';


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

  isDragging = false;
  isLoading: boolean = false;
  containerWidth?:number;
  containerHeight?:number;
  containerDepth?:number;
  selectedFiles:SelectedFile[] = []
  error:boolean = false;
  hasAllData = false;
  @ViewChild('fileUpload') fileUpload!: ElementRef;

  
  constructor(private router: Router, private organaizerService: OrganaizerService) {}

  ngAfterViewInit(): void {
    this.containerWidth = undefined;
    this.containerHeight = undefined;
    this.containerDepth = undefined;
    this.selectedFiles = [];
  }

  newExecution(): void {
    this.error = false;
    if (this.containerWidth && this.containerHeight && this.containerDepth && this.selectedFiles.length > 0) {
      this.isLoading = true;
      const w = this.containerWidth;
      const h = this.containerHeight;
      const d = this.containerDepth;
      this.organaizerService.presignedUrls(this.selectedFiles).subscribe({
        next: (resp:UploadImagesResponse) => {
          const urlsDictionary = resp.urls.reduce((acc, item) => {
              acc[item.id] = item.url;
              return acc;
          }, {} as { [key: string]: string });

          const execution:CreateExecutionRequest = {
            id: resp.id,
            container_width: w,
            container_height: h,
            container_depth: d
          }

          const uploads:Observable<Object>[] = []
          for (const selectedFile of this.selectedFiles) {
            uploads.push(this.organaizerService.uploadFile(urlsDictionary[selectedFile.id], selectedFile.file));
          }
          forkJoin(uploads).subscribe({
            complete: () => {
              this.isLoading = true;
              this.organaizerService.createExecution(execution).subscribe({
                next:() => this.router.navigate(['/']),
                error: (error) => {
                  this.isLoading = false;
                  alert(error);
                },
                complete: () => this.isLoading = false
              });
            },
            error: (error) => {
              this.isLoading = false;
              alert(error);
            },
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

  removeFile(selectedFile:SelectedFile):void {
    this.selectedFiles = this.selectedFiles.filter(sf => sf.id !== selectedFile.id);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  async onFilesSelected(event: any): Promise<void> {
    await this.addFiles(event.target.files);
  }

  async onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    
    if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length) {
      this.addFiles(event.dataTransfer.files);
    }
  }

  async onPaste(event: ClipboardEvent) {
    if (event?.clipboardData?.items) {
      const files: File[] = Array.from(event.clipboardData.items)
        .filter(item => item.type.startsWith('image/'))
        .map(item => item.getAsFile())
        .filter((file): file is File => file !== null);
        
      if (files.length > 0) {
        await this.addFiles(files);
      }
    }
  }

  private async addFiles(files: FileList | File[]) {
    if (!files || files.length == 0) {
      return;
    }
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      this.selectedFiles.push({
        id: uuidv4(),
        file: file,
        base64Content: await this.fileToBase64(file)
      });
    }
  }

  private async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
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
