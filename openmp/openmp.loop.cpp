#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <omp.h>
#include <string>

using namespace std;

struct Config {
  double t0 = 0;   // начало расчета в секундах
  double t1 = 10;  // конец расчета в секундах
  double Lx = 1.0; // длина области по x
  double Ly = 1.0; // длина области по y
  int Nx = 1024;   // количество узлов по x
  int Ny = 1024;   // количество узлов по y
  int N = 700;     // количество шагов по времени
  double a = 1;    // коэффициент температуропроводности
  bool debug = false;
  int loop = 1; // количество циклов раскрутки
};

double u_exact(double t, double x, double y, double Lx, double Ly) {
  return (1.0 + t) * cos(x * M_PI / Lx) * sin(y * M_PI / Ly);
}

double f(double t, double x, double y, double a, double Lx, double Ly) {
  return (1 + a * a * (1 + t) * M_PI * M_PI * (1 / (Lx * Lx) + 1 / (Ly * Ly))) *
         cos(x * M_PI / Lx) * sin(y * M_PI / Ly);
}

inline void update(const double *U, double *U_next, int i, int j, int Nx,
                   double rx, double ry) {
  int k = j * Nx + i;
  U_next[k] = U[k] + rx * (U[k + 1] - 2 * U[k] + U[k - 1]) +
              ry * (U[k - Nx] - 2 * U[k] + U[k + Nx]);
}

void relax(double *&U, Config &cfg) {
  int loop = cfg.loop;
  double t0 = cfg.t0;
  double t1 = cfg.t1;
  double Lx = cfg.Lx;
  double Ly = cfg.Ly;
  int Nx = cfg.Nx;
  int Ny = cfg.Ny;
  int N = cfg.N;
  double a = cfg.a;
  double tau = (t1 - t0) / N; // длительность одного шага
  double hx = Lx / (Nx - 1);  // шаг сетки по x;
  double hy = Ly / (Ny - 1);  // шаг сетки по y;
  double rx = (a * a * tau) / (hx * hx);
  double ry = (a * a * tau) / (hy * hy);
  double *U_next = new double[Nx * Ny]{};
  double start, end;

  // Начальное состояние
  for (int j = 0; j < Ny; j++) {
    for (int i = 0; i < Nx; i++) {
      double x = i * hx;
      double y = j * hy;
      U[j * Nx + i] = u_exact(t0, x, y, Lx, Ly);
    }
  }

#pragma omp parallel
  for (int n = 0; n < N; n++) {

    // Внутренние узлы
    if (cfg.debug) {
      double tn = t0 + n * tau;
#pragma omp for schedule(static)
      for (int j = 1; j < Ny - 1; j++) {
        for (int i = 1; i < Nx - 1; i++) {
          double x = i * hx;
          double y = j * hy;
          int k = j * Nx + i;
          U_next[k] = U[k] + rx * (U[k + 1] - 2 * U[k] + U[k - 1]) +
                      ry * (U[k - Nx] - 2 * U[k] + U[k + Nx]) +
                      tau * f(tn, x, y, a, Lx, Ly);
          // Граничные условия Неймана - второго рода
          U_next[j * Nx] = (4 * U_next[j * Nx + 1] - U_next[j * Nx + 2]) / 3;
          U_next[j * Nx + Nx - 1] =
              (4 * U_next[j * Nx + (Nx - 2)] - U_next[j * Nx + (Nx - 3)]) / 3;
        }
      }
    } else {
      switch (loop) {
      case 1: {
#pragma omp for schedule(static)
        for (int j = 1; j < Ny - 1; j++) {
          for (int i = 0; i + loop - 1 < Nx - 1; i++) {
            update(U, U_next, i, j, Nx, rx, ry);
            // Граничные условия Неймана - второго рода
            U_next[j * Nx] = (4 * U_next[j * Nx + 1] - U_next[j * Nx + 2]) / 3;
            U_next[j * Nx + Nx - 1] =
                (4 * U_next[j * Nx + (Nx - 2)] - U_next[j * Nx + (Nx - 3)]) / 3;
          }
        }
        break;
      }
      case 2: {
#pragma omp for schedule(static)
        for (int j = 1; j < Ny - 1; j++) {
          int i = 1;
          for (; i + loop - 1 < Nx - 1; i += 2) {
            update(U, U_next, i, j, Nx, rx, ry);
            update(U, U_next, i + 1, j, Nx, rx, ry);
          }
          for (; i < Nx - 1; i++) {
            update(U, U_next, i, j, Nx, rx, ry);
          }
          // Граничные условия Неймана - второго рода
          U_next[j * Nx] = (4 * U_next[j * Nx + 1] - U_next[j * Nx + 2]) / 3;
          U_next[j * Nx + Nx - 1] =
              (4 * U_next[j * Nx + (Nx - 2)] - U_next[j * Nx + (Nx - 3)]) / 3;
        }
        break;
      }
      case 4: {
#pragma omp for schedule(static)
        for (int j = 1; j < Ny - 1; j++) {
          int i = 1;
          for (; i + loop - 1 < Nx - 1; i += 4) {
            update(U, U_next, i, j, Nx, rx, ry);
            update(U, U_next, i + 1, j, Nx, rx, ry);
            update(U, U_next, i + 2, j, Nx, rx, ry);
            update(U, U_next, i + 3, j, Nx, rx, ry);
          }
          for (; i < Nx - 1; i++) {
            update(U, U_next, i, j, Nx, rx, ry);
          }
          // Граничные условия Неймана - второго рода
          U_next[j * Nx] = (4 * U_next[j * Nx + 1] - U_next[j * Nx + 2]) / 3;
          U_next[j * Nx + Nx - 1] =
              (4 * U_next[j * Nx + (Nx - 2)] - U_next[j * Nx + (Nx - 3)]) / 3;
        }
        break;
      }
      case 8: {
#pragma omp for schedule(static)
        for (int j = 1; j < Ny - 1; j++) {
          int i = 1;
          for (; i + loop - 1 < Nx - 1; i += 8) {
            update(U, U_next, i, j, Nx, rx, ry);
            update(U, U_next, i + 1, j, Nx, rx, ry);
            update(U, U_next, i + 2, j, Nx, rx, ry);
            update(U, U_next, i + 3, j, Nx, rx, ry);
            update(U, U_next, i + 4, j, Nx, rx, ry);
            update(U, U_next, i + 5, j, Nx, rx, ry);
            update(U, U_next, i + 6, j, Nx, rx, ry);
            update(U, U_next, i + 7, j, Nx, rx, ry);
          }
          for (; i < Nx - 1; i++) {
            update(U, U_next, i, j, Nx, rx, ry);
          }
          // Граничные условия Неймана - второго рода
          U_next[j * Nx] = (4 * U_next[j * Nx + 1] - U_next[j * Nx + 2]) / 3;
          U_next[j * Nx + Nx - 1] =
              (4 * U_next[j * Nx + (Nx - 2)] - U_next[j * Nx + (Nx - 3)]) / 3;
        }
        break;
      }
      }
    }

#pragma omp single
    {
      swap(U, U_next);
    }

    if (n == 0 && !cfg.debug) {
#pragma omp barrier

#pragma omp single
      {
        start = omp_get_wtime();
      }
    }
  }

  if (!cfg.debug) {
    end = omp_get_wtime();

    double time = std::chrono::duration<double>(end - start).count();

    double updates = double(N - 1) * (Nx - 2) * (Ny - 2);

    double mlups = updates / (time * 1e6);

    cout << "Time: " << time << " s\n";
    cout << "MLUPS: " << mlups // количество обработанных узлов сетки за секунду
         << endl;

    ofstream f("bechmark_omp_loop.csv", ios::app);
    f << loop << ";" << time << ";" << mlups << ";" << N << ";" << Nx << ";"
      << Ny << endl;
    f.close();
  }

  double checksum = 0.0;
  for (size_t k = 0; k < size_t(Nx) * Ny; ++k) {
    checksum += U[k] * U[k];
  }
  cout << "Checksum: " << checksum << '\n';

  delete[] U_next;
}

/*
 * Верификация решения
 * Сранивание численного (U) и аналитического решения (u_exact)
 * */
void verify(double *U, Config &cfg) {
  double Lx = cfg.Lx;
  double Ly = cfg.Ly;
  int Nx = cfg.Nx;
  int Ny = cfg.Ny;
  double t1 = cfg.t1;
  double hx = Lx / (Nx - 1); // шаг сетки по x;
  double hy = Ly / (Ny - 1); // шаг сетки по y;
  double error_inf = 0.0;
  double error_l2 = 0.0;

  for (int j = 0; j < Ny; j++) {
    for (int i = 0; i < Nx; i++) {
      double x = i * hx;
      double y = j * hy;

      double exact = u_exact(t1, x, y, Lx, Ly);
      double numeric = U[j * Nx + i];

      double error = abs(numeric - exact);

      error_inf = max(error_inf, error);
      error_l2 += error * error;
    }
  }

  error_l2 = sqrt(error_l2);

  cout << "C-норма: " << error_inf << endl;
  cout << "l2-норма: " << error_l2 << endl;
}

void validate(Config &cfg) {
  if (cfg.N <= 0 || cfg.Nx < 4 || cfg.Ny < 3 || cfg.t1 <= cfg.t0 ||
      cfg.Lx <= 0 || cfg.Ly <= 0 || cfg.a <= 0)
    throw invalid_argument("Некорректные параметры расчета");

  if (!cfg.debug && cfg.N < 2) {
    throw invalid_argument("Для измерения требуется минимум 2 шага");
  }

  double a = cfg.a;
  double T = cfg.t1 - cfg.t0;
  double Lx = cfg.Lx;
  double Ly = cfg.Ly;
  int N = cfg.N;
  int Nx = cfg.Nx;
  int Ny = cfg.Ny;
  double hx = Lx / (Nx - 1); // шаг сетки по x;
  double hy = Ly / (Ny - 1); // шаг сетки по y;
  double N_min = 2 * a * a * T * (1 / (hx * hx) + 1 / (hy * hy));

  if (N < N_min) {
    cout << "Условие устойчивости нарушено" << endl;
    cout << "Размер сетки: " << Nx << "x" << Ny << endl;
    cout << "Задано временных шагов: " << N << endl;
    cout << "Минимальное количество шагов: " << N_min << endl;
    exit(EXIT_FAILURE);
  } else {
    cout << "Условие устойчивости сохранено" << endl;
  }
}

void help(char *program) {
  cout << "Использование: " << program << " [параметры]\n\n"
       << "Параметры:\n"
       << "  --t0     Начальное время (0)\n"
       << "  --t1     Конечное время (10)\n"
       << "  --N      Количество шагов по времени (1000)\n"
       << "  --a      Температуропроводность (0.1)\n"
       << "  --Lx     Длина области по X (2.0)\n"
       << "  --Ly     Длина области по Y (1.0)\n"
       << "  --Nx     Количество узлов по X (100)\n"
       << "  --Ny     Количество узлов по Y (50)\n"
       << "  --debug  Включение режима отладки (0)\n"
       << "  --loop   Количество циклов раскрутки (1)\n"
       << "  -h, --help  Показать справку\n";
}

void parse(int argc, char *argv[], Config &cfg) {
  for (int i = 1; i < argc; ++i) {
    string arg = argv[i];

    if (i + 1 >= argc)
      throw invalid_argument("Нет значения для: " + arg);

    string value = argv[++i];

    if (arg == "--t0")
      cfg.t0 = stod(value);
    else if (arg == "--t1")
      cfg.t1 = stod(value);
    else if (arg == "--N")
      cfg.N = stoi(value);
    else if (arg == "--a")
      cfg.a = stod(value);
    else if (arg == "--Lx")
      cfg.Lx = stod(value);
    else if (arg == "--Ly")
      cfg.Ly = stod(value);
    else if (arg == "--Nx")
      cfg.Nx = stoi(value);
    else if (arg == "--Ny")
      cfg.Ny = stoi(value);
    else if (arg == "--debug")
      cfg.debug = value == "1" ? true : false;
    else if (arg == "--loop") {
      int loop = stoi(value);
      if (loop != 1 && loop != 2 && loop != 4 && loop != 8)
        throw invalid_argument("Допустимы 1, 2, 4, 8");
      cfg.loop = loop;
    } else {
      throw invalid_argument("Неизвестный аргумент: " + arg);
    }
  }
}

int main(int argc, char *argv[]) {
  if (argc == 1) {
    help(argv[0]);
    return EXIT_SUCCESS;
  }
  if (argc > 1) {
    string arg = argv[1];

    if (arg == "--help" || arg == "-h") {
      help(argv[0]);
      return EXIT_SUCCESS;
    }
  }

  Config cfg;

  try {
    parse(argc, argv, cfg);
  } catch (const exception &e) {
    cerr << "Ошибка: " << e.what() << endl;
    return 1;
  }

  validate(cfg);

  size_t size = cfg.Nx * cfg.Ny;
  double *U = new double[size]{};

  relax(U, cfg);

  if (cfg.debug == true) {
    verify(U, cfg);
  }

  delete[] U;
  return EXIT_SUCCESS;
}
