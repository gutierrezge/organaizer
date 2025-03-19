export interface Box {
    id:number
    execution_id:string
    x1:number
    x2:number
    y1:number
    y2:number
    width:number
    height:number
    depth:number
    volume:number
    inplan:boolean
    created_on:Date
    modified_on:Date
}
export interface Clp {
    execution_id:string
    box_id:number
    x:number
    y:number
    z:number
    created_on:Date
    modified_on:Date
}
export interface CreateExecutionRequest {
    id:string
    container_width:number
    container_height:number
    container_depth:number
}
export interface PredictedImage {
    id:string
    url:string
    boxes:Box[]
}
export interface Execution {
    id:string
    container_width:number
    container_height:number
    container_depth:number
    predicted_images: PredictedImage[]
    status:string
    status_message?:string
    created_on:Date
    modified_on:Date
    plan: Clp[]
    plan_remarks?:string
    total_boxes:number
    total_volume:number
}

export interface Executions {
    executions:Execution[]
}
export interface UploadImageRequest {
    id:string
    filename:string
}
export interface UploadImagesRequest {
    files: UploadImageRequest[]
}
export interface UploadImageResponse {
    id: string
    url: string
}

export interface UploadImagesResponse {
    id: string
    urls: UploadImageResponse[]
}

export interface SelectedFile {
    id: string
    file: File
    base64Content: string
}