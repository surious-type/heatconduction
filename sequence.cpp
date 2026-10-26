#include <cmath>
#include <cstdlib>
#include <iostream>

using namespace std;
float a = 0.1;  // коэффициент температуропроводности
float Lx = 2.0; // длина области по x
float Ly = 1.0; // длина области по y

float f(int t, float x, float y) {
  return ((1 + a * a * (1 + t) * M_PI * M_PI) *
          (1 / (Lx * Lx) + 1 / (Ly * Ly))) *
         cos(x * M_PI / Lx) * sin(y * M_PI / Ly);
}

int main(int argc, char *argv[]) {
  float t0 = 0;              // начало расчета в секундах
  float t1 = 10;             // конец расчета в секундах
  int N = 80;                // количество моментов времени
  float tau = (t1 - t0) / N; // длительность одного шага
  int Nx = 100;              // количество узлов по x
  int Ny = 50;               // количество узлов по y
  int Mx = Nx - 1;           // количество интервалов по x
  int My = Ny - 1;           // количество интервалов по y
  int hx = Lx / Mx;          // шаг сетки по x;
  int hy = Ly / My;          // шаг сетки по y;
  float *U_curr = new float[Lx * Ly]{};
  float *U_next = new float[Lx * Ly]{};

  for (int n = 0; n < N; n++) {
    float tn = t0 + n * tau;
    for (int j = 1; j < Ny - 1; j++) {
      for (int i = 1; i < Nx - 1; i++) {
        float rx = (a * a * tau) / (hx * hx);
        float ry = (a * a * tau) / (hy * hy);
        // Условие устойчивости
        if (rx + ry <= 0.5) {
          cout << "Условие устойчивости сохранено: ";
          cout << rx + ry << endl;
        }
        U_next[j * Nx + i] =
            U_curr[j * Nx + i] +
            rx * (U_curr[j * Nx + i + 1] - 2 * U_curr[j * Nx + i] +
                  U_curr[j * Nx + i - 1]) +
            ry * (U_curr[(j + 1) * Nx + i] - 2 * U_curr[j * Nx + i] +
                  U_curr[(j - 1) * Nx + i]) +
            tau * f(tn, i, j);
      }
    }
    // Граничные условия Неймана - второго рода
    for (int j = 1; j < Ny - 1; j++) {
      U_next[j * Nx] = (4 * U_next[j * Nx + 1] - U_next[j * Nx + 2]) / 3;
      U_next[j * Nx + Nx] =
          (4 * U_next[j * Nx + (Nx - 1)] - U_next[j * Nx + (Nx - 2)]) / 3;
    }

    for (int j = 1; j < Nx; j++) {
      for (int i = 1; i < Ny; i++) {

        cout << f(t1, )
      }
    }
  }

  return EXIT_SUCCESS;
}
