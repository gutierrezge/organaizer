import { HttpClient, HttpErrorResponse, HttpHeaders } from "@angular/common/http";
import { CreateExecutionRequest, Execution, Executions, PresignedUrlResponse } from "../models/models";
import { Injectable } from "@angular/core";
import { Observable, throwError } from "rxjs";
import { catchError } from 'rxjs/operators';


@Injectable({
    providedIn: 'root'
})
export class OrganaizerService {

    private ENDPOINT:string = "http://localhost:5000"
    execution?:Execution;

    constructor(private http: HttpClient) {
        this.resetExecution();
    }

    resetExecution() {
        this.execution = undefined;
    }

    private get<T>(path:string): Observable<T> {
        return this.http.get<T>(`${this.ENDPOINT}/${path}`).pipe(catchError(this.handleError));
    }
    private delete<T>(path:string): Observable<T> {
        return this.http.delete<T>(`${this.ENDPOINT}/${path}`).pipe(catchError(this.handleError));
    }
    private post<T>(path:string, body?:object): Observable<T> {
        return this.http.post<T>(`${this.ENDPOINT}/${path}`, body).pipe(catchError(this.handleError));
    }

    findAll(): Observable<Executions> {
        return this.get("executions");
    }

    findById(id:string): Observable<Execution> {
        return this.get(`execution/${id}`);
    }

    presignedUrls(filename:string): Observable<PresignedUrlResponse> {
        return this.post("presigned-put-url", {"key": filename});
    }

    redo(execution:Execution): Observable<Execution> {
        return this.post(`rerun/${execution.id}`);
    }

    deleteExecution(execution:Execution): Observable<Execution> {
        return this.delete(`execution/${execution.id}`);
    }

    uploadFile(presignedUrl:string, file:File): Observable<Object> {
        return this.http.put(presignedUrl, file, { headers: { 'Content-Type': file.type, 'x-amz-acl': 'public-read'} });
    }

    createExecution(execution:CreateExecutionRequest): Observable<Execution> {
        return this.post("execution", execution);
    }

    // create(chat:ChatEntity): Observable<ApiResponse<ChatEntity>> {
    //     return this.request("create-chat", {"chat": chat});
    // }

    private handleError(error: HttpErrorResponse) {
        if (error.error instanceof ErrorEvent) {
            console.error('An error occurred:', error.error.message);
        } else {
            console.error(`Backend returned code ${error.status}, body was: ${error.error}`);
        }
        return throwError(() => new Error('Something bad happened; please try again later.'));
    }

}