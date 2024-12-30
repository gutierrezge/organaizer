import { Routes } from '@angular/router';
import { ExecutionListComponent } from './execution-list/execution-list.component';
import { NewExecutionComponent } from './new-execution/new-execution.component';

export const routes: Routes = [
    { path: '', component: ExecutionListComponent},
    { path: 'new', component: NewExecutionComponent},
];
