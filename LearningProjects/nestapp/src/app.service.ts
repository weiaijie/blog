/*
 * @Description: 
 * @Author: xuhui
 * @Date: 2023-09-21 23:36:48
 * @LastEditors: weiaijie
 * @FilePath: \blog\LearningProjects\nestapp\src\app.service.ts
 */
import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  getHello(): string {
    return 'Hello World1111!';
  }
}
