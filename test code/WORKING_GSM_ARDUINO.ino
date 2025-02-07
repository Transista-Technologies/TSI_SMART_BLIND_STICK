#include "pico/stdlib.h"
#include "hardware/uart.h"

#define TX_PIN 0  // GPIO 0 (Change if needed)
#define RX_PIN 1  // GPIO 1 (Change if needed)
#define BAUD_RATE 115200

#define PHONE_NUMBER "+916374025417"  // Replace with actual recipient number
#define MESSAGE "Yov work aagudhu"

// Initialize UART0 for EC200U
#define GSM_UART uart0

void send_at_command(const char *command, int delay_ms) {
    uart_puts(GSM_UART, command);
    uart_puts(GSM_UART, "\r\n");  // Send command with newline
    sleep_ms(delay_ms);

    while (uart_is_readable(GSM_UART)) {
        char c = uart_getc(GSM_UART);
        putchar(c);  // Print response to serial monitor
    }
}

void send_sms() {
    printf("Setting SMS to text mode...\n");
    send_at_command("AT+CMGF=1", 1000);

    printf("Setting recipient number: %s\n", PHONE_NUMBER);
    String cmgsCommand = "AT+CMGS=\"" + String(PHONE_NUMBER) + "\"";
    send_at_command(cmgsCommand.c_str(), 2000);

    printf("Sending message...\n");
    uart_puts(GSM_UART, MESSAGE);
    uart_putc(GSM_UART, 0x1A);  // CTRL+Z to send
    sleep_ms(5000);  // Wait for SMS to send

    while (uart_is_readable(GSM_UART)) {
        char c = uart_getc(GSM_UART);
        putchar(c);  // Print response to serial monitor
    }
}

void setup() {
    Serial.begin(115200);  // Start Serial Monitor
    uart_init(GSM_UART, BAUD_RATE);
    gpio_set_function(TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(RX_PIN, GPIO_FUNC_UART);

    send_sms();
}

void loop() {
    delay(1000);
}
