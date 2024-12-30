export interface Box {
    execution_id:string
    x1:number
    x2:number
    y1:number
    y2:number
    width:number
    height:number
    depth:number
    volume:number
    created_on:Date
    modified_on:Date
}
export interface CreateExecutionRequest {
    id:string
    key:string
    container_width:number
    container_height:number
    container_depth:number
}
export interface Execution {
    id:string
    key:string
    container_width:number
    container_height:number
    container_depth:number
    status:string
    status_message?:number
    created_on:Date
    modified_on:Date
    boxes:Box[]
    total_boxes:number
    total_volume:number
}

export interface Executions {
    executions:Execution[]
}

export interface PresignedUrlResponse {
    id: string
    key: string
    url: string
    expiration: number
}