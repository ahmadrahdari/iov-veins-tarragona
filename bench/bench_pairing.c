/* Execution time of the primitives of the handover schemes compared in Table VII,
 * on the platform of Table V and with the same OpenSSL 3 big-number arithmetic:
 *   Tpm : scalar multiplication on secp160r1 (reference, as in bench.c)
 *   Te  : scalar multiplication (exponentiation) in G of a Type-A pairing, i.e., on
 *         y^2 = x^3 + x over a 512-bit prime field q = 3 mod 4, subgroup order r of 160 bits
 *   Tbp : Tate pairing e: G x G -> GT with the distortion map (x,y) -> (-x, iy),
 *         Miller loop in Jacobian coordinates with denominator elimination and
 *         final exponentiation (q^2-1)/r
 *   Tc  : Chebyshev polynomial T_n(x) mod p with a 512-bit prime p and a 160-bit n
 * Both 512-bit settings give the 80-bit level of secp160r1, since discrete logarithms in
 * GT and in the Chebyshev semigroup reduce to those in a field of 1024 bits.
 * All times are CPU times of this process, so that other processes on the machine do not
 * inflate them; the program also prints Te, Tbp, and Tc relative to Tpm.
 * Build: gcc -O2 bench_pairing.c -o bench_pairing -lcrypto
 */
#include <stdio.h>
#include <time.h>
#include <openssl/bn.h>
#include <openssl/ec.h>
#include <openssl/obj_mac.h>

static double cpu(void) {
    struct timespec t; clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

static BN_CTX *ctx; static BIGNUM *q, *r, *h; static BN_MONT_CTX *mont;
static BIGNUM *one_m;   /* 1 in Montgomery form */

/* F_q in Montgomery form */
static void fm(BIGNUM *z, const BIGNUM *a, const BIGNUM *b) { BN_mod_mul_montgomery(z, a, b, mont, ctx); }
static void fa(BIGNUM *z, const BIGNUM *a, const BIGNUM *b) { BN_mod_add_quick(z, a, b, q); }
static void fs(BIGNUM *z, const BIGNUM *a, const BIGNUM *b) { BN_mod_sub_quick(z, a, b, q); }

/* F_q^2 = F_q[i]/(i^2+1) */
typedef struct { BIGNUM *a, *b; } fp2;
static void f2_init(fp2 *x) { x->a = BN_new(); x->b = BN_new(); }
static void f2_copy(fp2 *z, const fp2 *x) { BN_copy(z->a, x->a); BN_copy(z->b, x->b); }
static BIGNUM *t0, *t1, *t2, *t3;
static void f2_mul(fp2 *z, const fp2 *x, const fp2 *y) {
    fm(t0, x->a, y->a); fm(t1, x->b, y->b);
    fa(t2, x->a, x->b); fa(t3, y->a, y->b); fm(t2, t2, t3);
    fs(z->a, t0, t1); fs(t2, t2, t0); fs(z->b, t2, t1);
}
static void f2_sqr(fp2 *z, const fp2 *x) {
    fa(t0, x->a, x->b); fs(t1, x->a, x->b); fm(t2, x->a, x->b);
    fm(z->a, t0, t1); fa(z->b, t2, t2);
}
static void f2_inv(fp2 *z, const fp2 *x) {   /* (a - bi) / (a^2 + b^2) */
    fm(t0, x->a, x->a); fm(t1, x->b, x->b); fa(t0, t0, t1);
    BN_from_montgomery(t0, t0, mont, ctx); BN_mod_inverse(t0, t0, q, ctx); BN_to_montgomery(t0, t0, mont, ctx);
    fm(z->a, x->a, t0); fm(t1, x->b, t0); BN_sub(z->b, q, t1); if (BN_cmp(z->b, q) == 0) BN_zero(z->b);
}
static int f2_eq(const fp2 *x, const fp2 *y) { return !BN_cmp(x->a, y->a) && !BN_cmp(x->b, y->b); }
static void f2_pow(fp2 *z, const fp2 *x, const BIGNUM *e) {
    fp2 acc; f2_init(&acc); BN_copy(acc.a, one_m); BN_zero(acc.b);
    for (int i = BN_num_bits(e) - 1; i >= 0; i--) { f2_sqr(&acc, &acc); if (BN_is_bit_set(e, i)) f2_mul(&acc, &acc, x); }
    f2_copy(z, &acc); BN_free(acc.a); BN_free(acc.b);
}

/* Tate pairing e(P, psi(Q)); P, Q given in affine coordinates, Montgomery form */
static BIGNUM *X, *Y, *Z, *M, *S, *u, *v, *w, *xt, *yt, *lam;
static void pairing(fp2 *res, const BIGNUM *xp, const BIGNUM *yp, const BIGNUM *xq, const BIGNUM *yq) {
    fp2 f, l; f2_init(&f); f2_init(&l);
    BN_copy(f.a, one_m); BN_zero(f.b);
    BN_copy(X, xp); BN_copy(Y, yp); BN_copy(Z, one_m);
    for (int i = BN_num_bits(r) - 2; i >= 0; i--) {
        /* doubling step with the tangent line at psi(Q) = (-xq, i*yq):
           l = M(xq Z^2 + X) - 2Y^2 + i * yq * 2Y Z^3,  M = 3X^2 + Z^4 */
        fm(u, Z, Z);                       /* Z^2 */
        fm(v, u, u);                       /* Z^4 */
        fm(M, X, X); fa(w, M, M); fa(M, w, M); fa(M, M, v);
        fm(w, Y, Y);                       /* Y^2 */
        fm(t0, xq, u); fa(t0, t0, X); fm(l.a, M, t0); fs(l.a, l.a, w); fs(l.a, l.a, w);
        fm(t0, Y, Z); fa(t0, t0, t0);      /* Z3 = 2YZ */
        fm(t1, t0, u); fm(l.b, yq, t1);
        fm(S, X, w); fa(S, S, S); fa(S, S, S);           /* S = 4XY^2 */
        fm(t1, M, M); fs(t1, t1, S); fs(t1, t1, S);      /* X3 = M^2 - 2S */
        fm(t2, w, w); fa(t2, t2, t2); fa(t2, t2, t2); fa(t2, t2, t2);  /* 8Y^4 */
        fs(t3, S, t1); fm(t3, M, t3); fs(Y, t3, t2);
        BN_copy(X, t1); BN_copy(Z, t0);
        f2_sqr(&f, &f); f2_mul(&f, &f, &l);
        if (BN_is_bit_set(r, i) && i > 0) {   /* addition step with P (affine); the last one is vertical */
            BN_from_montgomery(t0, Z, mont, ctx); BN_mod_inverse(t0, t0, q, ctx); BN_to_montgomery(t0, t0, mont, ctx);
            fm(t1, t0, t0); fm(xt, X, t1); fm(t1, t1, t0); fm(yt, Y, t1);
            fs(t0, xp, xt); BN_from_montgomery(t0, t0, mont, ctx); BN_mod_inverse(t0, t0, q, ctx); BN_to_montgomery(t0, t0, mont, ctx);
            fs(lam, yp, yt); fm(lam, lam, t0);
            fa(t1, xq, xt); fm(l.a, lam, t1); fs(l.a, l.a, yt); BN_copy(l.b, yq);
            f2_mul(&f, &f, &l);
            fm(t1, lam, lam); fs(t1, t1, xt); fs(t1, t1, xp);          /* x3 */
            fs(t2, xt, t1); fm(t2, lam, t2); fs(Y, t2, yt);           /* y3 */
            BN_copy(X, t1); BN_copy(Z, one_m);
        }
    }
    /* final exponentiation: f^(q-1) = conj(f)/f, then ^((q+1)/r) */
    fp2 g; f2_init(&g); f2_inv(&g, &f);
    BN_sub(f.b, q, f.b); if (BN_cmp(f.b, q) == 0) BN_zero(f.b);
    f2_mul(&g, &f, &g);
    f2_pow(res, &g, h);
    BN_free(f.a); BN_free(f.b); BN_free(l.a); BN_free(l.b); BN_free(g.a); BN_free(g.b);
}

/* Chebyshev polynomial T_n(x) mod q (Montgomery form): T_2k = 2T_k^2 - 1, T_2k+1 = 2T_k T_k+1 - x */
static BIGNUM *ca, *cb, *two_m;
static void cheb(BIGNUM *z, const BIGNUM *x, const BIGNUM *n) {
    BN_copy(ca, x); fm(cb, x, x); fa(cb, cb, cb); fs(cb, cb, one_m);   /* (T_1, T_2) */
    for (int i = BN_num_bits(n) - 2; i >= 0; i--) {
        fm(t0, ca, cb); fa(t0, t0, t0); fs(t0, t0, x);                 /* T_2k+1 */
        if (BN_is_bit_set(n, i)) { fm(t1, cb, cb); fa(t1, t1, t1); fs(cb, t1, one_m); BN_copy(ca, t0); }
        else { fm(t1, ca, ca); fa(t1, t1, t1); fs(ca, t1, one_m); BN_copy(cb, t0); }
    }
    BN_copy(z, ca);
}

#define N 200
#define ROUNDS 10
int main(void) {
    ctx = BN_CTX_new(); q = BN_new(); r = BN_new(); h = BN_new();
    BIGNUM **regs[] = {&t0, &t1, &t2, &t3, &X, &Y, &Z, &M, &S, &u, &v, &w, &xt, &yt, &lam, &ca, &cb, &two_m, &one_m};
    for (unsigned i = 0; i < sizeof regs / sizeof *regs; i++) *regs[i] = BN_new();
    /* r = 2^159 + 2^107 + 1 (the Solinas prime of PBC's Type-A curves); q = h r - 1 prime, q = 3 mod 4 */
    BN_set_bit(r, 159); BN_set_bit(r, 107); BN_set_bit(r, 0);
    if (BN_check_prime(r, ctx, NULL) != 1) { puts("r not prime"); return 1; }
    do {
        BN_rand(h, 353, BN_RAND_TOP_ONE, BN_RAND_BOTTOM_ANY);
        BN_rshift(h, h, 2); BN_lshift(h, h, 2);            /* 4 | h  =>  q = 3 mod 4 */
        BN_mul(q, h, r, ctx); BN_sub_word(q, 1);
    } while (BN_num_bits(q) != 512 || BN_check_prime(q, ctx, NULL) != 1);
    fprintf(stderr, "params ok\n");
    mont = BN_MONT_CTX_new(); BN_MONT_CTX_set(mont, q, ctx);
    BN_one(t0); BN_to_montgomery(one_m, t0, mont, ctx);

    /* the curve y^2 = x^3 + x through OpenSSL, for Te and for point arithmetic */
    BIGNUM *a = BN_new(), *b = BN_new(); BN_one(a); BN_zero(b);
    EC_GROUP *G = EC_GROUP_new_curve_GFp(q, a, b, ctx);
    EC_POINT *P = EC_POINT_new(G), *Q = EC_POINT_new(G), *T = EC_POINT_new(G);
    BIGNUM *x = BN_new(), *y = BN_new(), *e = BN_new();
    BN_add_word(h, 0);
    for (;;) {   /* random point, then multiply by the cofactor h */
        BN_rand_range(x, q);
        BN_mod_sqr(y, x, q, ctx); BN_add_word(y, 1); BN_mod_mul(y, y, x, q, ctx);       /* x^3 + x */
        BN_copy(e, q); BN_add_word(e, 1); BN_rshift(e, e, 2); BN_mod_exp(t0, y, e, q, ctx);
        BN_mod_sqr(t1, t0, q, ctx);
        if (BN_cmp(t1, y) == 0 && EC_POINT_set_affine_coordinates(G, T, x, t0, ctx)) break;
    }
    fprintf(stderr, "point ok\n");
    EC_POINT_mul(G, P, NULL, T, h, ctx);
    EC_GROUP_set_generator(G, P, r, h);
    BIGNUM *ka = BN_new(), *kb = BN_new(), *kab = BN_new();
    BN_rand_range(ka, r); BN_rand_range(kb, r); BN_mod_mul(kab, ka, kb, r, ctx);

    /* correctness: e(aP, bP) = e(P, P)^(ab) and e(P, P) != 1 */
    BIGNUM *xa = BN_new(), *ya = BN_new(), *xb = BN_new(), *yb = BN_new();
    EC_POINT_mul(G, T, NULL, P, ka, ctx); EC_POINT_get_affine_coordinates(G, T, xa, ya, ctx);
    EC_POINT_mul(G, Q, NULL, P, kb, ctx); EC_POINT_get_affine_coordinates(G, Q, xb, yb, ctx);
    EC_POINT_get_affine_coordinates(G, P, x, y, ctx);
    BN_to_montgomery(xa, xa, mont, ctx); BN_to_montgomery(ya, ya, mont, ctx);
    BN_to_montgomery(xb, xb, mont, ctx); BN_to_montgomery(yb, yb, mont, ctx);
    BN_to_montgomery(x, x, mont, ctx); BN_to_montgomery(y, y, mont, ctx);
    fp2 e1, e2, e3; f2_init(&e1); f2_init(&e2); f2_init(&e3);
    pairing(&e1, xa, ya, xb, yb); pairing(&e2, x, y, x, y); f2_pow(&e3, &e2, kab);
    int ok = f2_eq(&e1, &e3) && !(BN_cmp(e2.a, one_m) == 0 && BN_is_zero(e2.b));
    printf("bilinearity check: %s\n", ok ? "ok" : "FAILED"); fflush(stdout);
    if (!ok) return 1;
    /* Chebyshev semigroup check: T_a(T_b(x)) = T_ab(x) for integers a, b */
    BIGNUM *cx = BN_new(), *c1 = BN_new(), *c2 = BN_new(), *n160[64];
    BN_rand_range(cx, q); BN_to_montgomery(cx, cx, mont, ctx);
    BIGNUM *sa = BN_new(), *sb = BN_new(), *sab = BN_new();
    BN_rand(sa, 80, BN_RAND_TOP_ONE, BN_RAND_BOTTOM_ANY); BN_rand(sb, 80, BN_RAND_TOP_ONE, BN_RAND_BOTTOM_ANY); BN_mul(sab, sa, sb, ctx);
    cheb(c1, cx, sb); cheb(c1, c1, sa); cheb(c2, cx, sab);
    printf("Chebyshev check: %s\n", BN_cmp(c1, c2) == 0 ? "ok" : "FAILED"); fflush(stdout);
    for (int i = 0; i < 64; i++) { n160[i] = BN_new(); BN_rand(n160[i], 160, BN_RAND_TOP_ONE, BN_RAND_BOTTOM_ANY); }

    /* reference: secp160r1 */
    EC_GROUP *G160 = EC_GROUP_new_by_curve_name(NID_secp160r1);
    EC_POINT *P160 = EC_POINT_new(G160), *Z160 = EC_POINT_new(G160);
    BIGNUM *k160[64]; const BIGNUM *o160 = EC_GROUP_get0_order(G160);
    for (int i = 0; i < 64; i++) { k160[i] = BN_new(); BN_rand_range(k160[i], o160); }
    EC_POINT_mul(G160, P160, k160[1], NULL, NULL, ctx);
    BIGNUM *kr[64]; for (int i = 0; i < 64; i++) { kr[i] = BN_new(); BN_rand_range(kr[i], r); }

    double s[4] = {0}, ss[4] = {0};
    for (int rd = 0; rd < ROUNDS; rd++) {
        double t, m[4];
        t = cpu(); for (int i = 0; i < N; i++) EC_POINT_mul(G160, Z160, NULL, P160, k160[i & 63], ctx); m[0] = (cpu() - t) / N;
        t = cpu(); for (int i = 0; i < N; i++) EC_POINT_mul(G, T, NULL, Q, kr[i & 63], ctx); m[1] = (cpu() - t) / N;
        t = cpu(); for (int i = 0; i < N / 4; i++) pairing(&e1, xa, ya, xb, yb); m[2] = (cpu() - t) / (N / 4);
        t = cpu(); for (int i = 0; i < N; i++) cheb(c1, cx, n160[i & 63]); m[3] = (cpu() - t) / N;
        for (int j = 0; j < 4; j++) { s[j] += m[j]; ss[j] += m[j] * m[j]; }
        fprintf(stderr, "round %d: %.4f %.4f %.4f %.4f ms\n", rd, m[0]*1e3, m[1]*1e3, m[2]*1e3, m[3]*1e3);
    }
    const char *nm[4] = {"Tpm (secp160r1)", "Te  (Type-A G)", "Tbp (Tate)", "Tc  (Chebyshev)"};
    printf("{\n");
    for (int j = 0; j < 4; j++) {
        double mu = s[j] / ROUNDS;
        printf(" \"%s\": {\"ms\": %.5f, \"ratio_to_Tpm\": %.3f}%s\n", nm[j], mu * 1e3, mu / (s[0] / ROUNDS), j < 3 ? "," : "");
    }
    printf("}\n");
    return 0;
}
