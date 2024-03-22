/*
 * uart.c
 *
 *  Created on: Mar 11, 2024
 *      Author: kccistc
 */

#include "uart.h"
#include <stdio.h>

UART_HandleTypeDef *myHuart;

#define rxBufferMax 255

int rxBufferGp;			// get pointer (read)
int rxBufferPp;			// put pointer (write)
uint8_t rxBuffer[rxBufferMax];
uint8_t rxChar;

// init device
void initUart(UART_HandleTypeDef *inHuart) {
	myHuart = inHuart;
	HAL_UART_Receive_IT(myHuart, &rxChar, 1);	//	문자 하나 수신할 때마다 HAL_UART_RxCpltCallback호출
}

// process received charactor
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
	rxBuffer[rxBufferPp++] = rxChar;						//buffer가 꽉 찰 때까지 반복 됨
	rxBufferPp %= rxBufferMax;
	HAL_UART_Receive_IT(myHuart, &rxChar, 1);
}

// get charactor from buffer
int16_t getChar() {
	int16_t result;
	if (rxBufferGp == rxBufferPp)	return -1;	//
	result = rxBuffer[rxBufferGp++];				//
	rxBufferGp %= rxBufferMax;
	return result;
}

int _write(int file, char *p, int len) {
	HAL_UART_Transmit(myHuart, p, len, 10); // lcd, uart, ...
	return len;
}

// packet transmit
void transmitPacket(protocol_t data){		// binary data
	// 사전 준비
	uint8_t txBuffer[] = {STX, 0, 0, 0, 0, ETX};
	txBuffer[1] = data.command;
	txBuffer[2] = (data.data >> 7) | 0x80;
	txBuffer[3] = (data.data & 0x7f) | 0x80;
	// CRC 계산
	txBuffer[4] = txBuffer[0] + txBuffer[1] + txBuffer[2] + txBuffer[3];
	// 데이터 전송
	HAL_UART_Transmit(myHuart, txBuffer, sizeof(txBuffer), 1);
	// 데이터 전송 완료 대기
	while((HAL_UART_GetState(myHuart) == HAL_UART_STATE_BUSY_TX)		// TX 중인 상태
			|| (HAL_UART_GetState(myHuart) == HAL_UART_STATE_BUSY_TX_RX));
}

// packet receive
protocol_t receivePacket(){
	protocol_t result;
	uint8_t buffer[6];
	uint8_t count = 0;
	uint32_t timeout;

	int16_t ch = getChar();
	memset(&result, 0, sizeof(buffer));
	if(ch == STX) {
		buffer[count++] = ch;

		// timeout start
		timeout = HAL_GetTick();		// systemtick : 1ms마다 count
																// HAL_GetTick : get count value

		while(ch != ETX) 						// ch != ETX면 무한 반복
		{
			ch = getChar();
			if(ch != -1)							// if data exist
			{
				buffer[count++] = ch;
			}

		// timeout calculate
			if(HAL_GetTick() - timeout >= 2) return result;// command = 0 일 경우 데이터 수신x
		}
		// 데이터 1 byte 당 0.8us (1/11520)
		// 6byte packet data : 0.8 * 6 = 4.8us
		// 2ms로 여유

		// serial protocol 상 (start bit + 8bit data + stop bit) 10bit:1byte
		// 115,200/10 = 11520 바이트 데이터 수신

		// CRC 검사
		uint8_t crc = 0;
		for(int i = 0; i < 4; i++)
			crc += buffer[i];
		if(crc != buffer[4]) return result;// command = 0 일 경우 데이터 수신x

		// after receiving, parsing
		result.command = buffer[1];
		result.data = buffer[3] & 0x7f;
		result.data |= (buffer[2] & 0x7f) << 7;
	}
	return result;		// command = 0 일 경우 데이터 수신x
}


