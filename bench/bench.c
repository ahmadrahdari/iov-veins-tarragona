/* Execution time of the cryptographic operations used in the cost comparison.
 * All operations are measured on the same machine with OpenSSL 3:
 *   Tpm : scalar multiplication k*P of an arbitrary point on secp160r1
 *   Tpa : point addition P+Q on secp160r1
 *   Th  : SHA-1 of a 128-byte input (160-bit output)
 *   Tsed: AES-128-CTR encryption of a 16-byte block, including the key schedule
 *   Tmm : 160-bit modular multiplication (BN_mod_mul)
 * plus a Horner evaluation of a degree-t polynomial over F_q (t = 100, 1000).
 * Each operation is repeated N times after a warm-up; the program reports the
 * mean over R rounds and the standard deviation of the round means.
 * Build: gcc -O2 bench.c -o bench -lcrypto
 */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <openssl/ec.h>
#include <openssl/obj_mac.h>
#include <openssl/bn.h>
#include <openssl/evp.h>
#include <openssl/rand.h>

static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

#define R 20

static EC_GROUP *grp; static BN_CTX *ctx; static BIGNUM *k[64], *q, *a[64], *b[64], *coef[1001], *x;
static EC_POINT *P, *Q, *Z;
static unsigned char msg[128], key[16], iv[16], blk[16], out[32], dig[20];
static volatile unsigned sink;

static void op_pm(int i)   { EC_POINT_mul(grp, Z, NULL, P, k[i & 63], ctx); }
static void op_pa(int i)   { (void)i; EC_POINT_add(grp, Z, P, Q, ctx); }
static void op_h(int i)    { msg[0] = (unsigned char)i; unsigned l; EVP_Digest(msg, sizeof msg, dig, &l, EVP_sha1(), NULL); sink += dig[0]; }
static void op_sed(int i) {
    key[0] = (unsigned char)i; int l1, l2;
    EVP_CIPHER_CTX *c = EVP_CIPHER_CTX_new();
    EVP_EncryptInit_ex(c, EVP_aes_128_ctr(), NULL, key, iv);
    EVP_EncryptUpdate(c, out, &l1, blk, 16);
    EVP_EncryptFinal_ex(c, out + l1, &l2);
    EVP_CIPHER_CTX_free(c); sink += out[0];
}
static BIGNUM *r_;
static void op_mm(int i)   { BN_mod_mul(r_, a[i & 63], b[i & 63], q, ctx); }
static int deg;
static void op_poly(int i) {   /* Horner: y = (...(c_t x + c_{t-1}) x + ...) + c_0 mod q */
    (void)i; BN_copy(r_, coef[deg]);
    for (int j = deg - 1; j >= 0; j--) { BN_mod_mul(r_, r_, x, q, ctx); BN_mod_add(r_, r_, coef[j], q, ctx); }
}

static void bench(const char *name, void (*f)(int), int n) {
    for (int i = 0; i < n / 10 + 1; i++) f(i);                 /* warm-up */
    double m[R], s = 0, v = 0;
    for (int r = 0; r < R; r++) {
        double t0 = now();
        for (int i = 0; i < n; i++) f(i);
        m[r] = (now() - t0) / n * 1e3; s += m[r];             /* ms per operation */
    }
    s /= R; for (int r = 0; r < R; r++) v += (m[r] - s) * (m[r] - s);
    printf("%-6s %12.6f ms  (sd %.6f, %d x %d runs)\n", name, s, sqrt(v / (R - 1)), R, n);
}

int main(void) {
    grp = EC_GROUP_new_by_curve_name(NID_secp160r1); ctx = BN_CTX_new();
    const BIGNUM *n = EC_GROUP_get0_order(grp);
    P = EC_POINT_new(grp); Q = EC_POINT_new(grp); Z = EC_POINT_new(grp);
    BIGNUM *t = BN_new(); BN_rand_range(t, n); EC_POINT_mul(grp, P, t, NULL, NULL, ctx);
    BN_rand_range(t, n); EC_POINT_mul(grp, Q, t, NULL, NULL, ctx);
    q = BN_new(); BN_generate_prime_ex(q, 160, 0, NULL, NULL, NULL);
    for (int i = 0; i < 64; i++) {
        k[i] = BN_new(); BN_rand_range(k[i], n);
        a[i] = BN_new(); BN_rand_range(a[i], q); b[i] = BN_new(); BN_rand_range(b[i], q);
    }
    for (int i = 0; i <= 1000; i++) { coef[i] = BN_new(); BN_rand_range(coef[i], q); }
    x = BN_new(); BN_rand_range(x, q); r_ = BN_new();
    RAND_bytes(msg, sizeof msg); RAND_bytes(key, 16); RAND_bytes(iv, 16); RAND_bytes(blk, 16);

    printf("OpenSSL %s, curve secp160r1 (|n| = %d bits), |q| = %d bits\n",
           OpenSSL_version(OPENSSL_VERSION), BN_num_bits(n), BN_num_bits(q));
    bench("Tpm", op_pm, 2000);
    bench("Tpa", op_pa, 20000);
    bench("Th", op_h, 200000);
    bench("Tsed", op_sed, 100000);
    bench("Tmm", op_mm, 500000);
    deg = 100;  bench("f_100", op_poly, 2000);
    deg = 1000; bench("f_1000", op_poly, 200);
    return 0;
}
