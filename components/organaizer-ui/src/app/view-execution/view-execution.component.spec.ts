import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewExecutionComponent } from './view-execution.component';

describe('ViewExecutionComponent', () => {
  let component: ViewExecutionComponent;
  let fixture: ComponentFixture<ViewExecutionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ViewExecutionComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ViewExecutionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
