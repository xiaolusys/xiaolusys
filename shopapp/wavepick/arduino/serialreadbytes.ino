#define BUFSIZE 24
char buf1[BUFSIZE];
char buf2[BUFSIZE];

int light_a[][8] = {
 3,15,-1,-1,-1,-1,-1,-1, 
 0, 1, 3, 5, 6,15,-1,-1,
 0, 3, 4,-1,-1,-1,-1,-1,
 0, 3, 6,-1,-1,-1,-1,-1,
 1, 3, 5, 6,-1,-1,-1,-1,
 2, 3, 6,-1,-1,-1,-1,-1,
 2, 3,-1,-1,-1,-1,-1,-1,
 0, 3, 5, 6,15,-1,-1,-1,
 3,-1,-1,-1,-1,-1,-1,-1,
 3, 6,-1,-1,-1,-1,-1,-1,
 0, 1, 2, 3, 4, 5, 6,15
};

int light_b[][8] = {
 7,11,-1,-1,-1,-1,-1,-1,
 7, 8, 9,11,13,14,-1,-1,
 8,11,12,-1,-1,-1,-1,-1,
 8,11,14,-1,-1,-1,-1,-1,
 9,11,13,14,-1,-1,-1,-1,
10,11,14,-1,-1,-1,-1,-1,
10,11,-1,-1,-1,-1,-1,-1,
 7, 8,11,13,14,-1,-1,-1,
11,-1,-1,-1,-1,-1,-1,-1,
11,14,-1,-1,-1,-1,-1,-1,
 7, 8, 9,10,11,12,13,14
};

// latchpin, clockpin, datapin
int pins[][3] = {
11,12,13,
 8, 9, 10,
 5, 6, 7,
 2, 3, 4
};

int requested = 0;

void setup() {                
  Serial.begin(9600);

  for (int i=0;i<4;i++)
  for (int j=0;j<3;j++)
    pinMode(pins[i][j], OUTPUT); 

}

void display(int a, int b, int x) {
  int clockPin = pins[x][0];  
  int latchPin = pins[x][1];
  int dataPin  = pins[x][2];


  for (int led = 0; led < 16; led++) {
    int numberToDisplay  = 0;
    for (int i=0; i<8; i++){
      if (led == light_a[a][i] || led == light_b[b][i]) {
        numberToDisplay = 1;
      } 
    }

    byte high_Byte = highByte(numberToDisplay);
    byte low_Byte = lowByte(numberToDisplay);
     

    // 送資料前要先把 latchPin 拉成低電位
    digitalWrite(latchPin, LOW);

    
    // 先送高位元組 (Hight Byte), 給離 Arduino 較遠的那顆 74HC595
    shiftOut(dataPin, clockPin, MSBFIRST, high_Byte);  
    // 再送低位元組 (Low Byte), 給離 Arduino 較近的那顆 74HC595
    shiftOut(dataPin, clockPin, MSBFIRST, low_Byte);  
    // 送完資料後要把 latchPin 拉回成高電位
    digitalWrite(latchPin, HIGH);
    
  }
}


void loop() {
  if (Serial.available() > 0) {
    memset(buf2,0,BUFSIZE);
    Serial.readBytes(buf2, BUFSIZE);
    if (memcmp(buf1,buf2,BUFSIZE) != 0) {
      memcpy(buf1,buf2,BUFSIZE);
      for (int i=0; i<24; i=i+2) {
        int a = buf1[i]   - '0';
        int b = buf1[i+1] - '0';

        if (a == 0) {
          a = 10;
          if (b == 0) {
            b = 10;
	  }
        }
        display(a,b,0);
      }
    } else {
      delay(100);
    }
    requested = 0;
  } else {
    if (requested == 0) {
      Serial.print('r');
      requested = 1;
    }
    delay(100);
  }
}
