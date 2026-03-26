/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./core/templates/**/*.html",
    "./**/templates/**/*.html",
    "./static/src/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        tinta: "#0f172a",
        rio: "#114b5f",
        espuma: "#f5fbff",
        mango: "#f7b267",
        menta: "#7bd389",
      },
      boxShadow: {
        suave: "0 18px 45px -22px rgba(17, 75, 95, 0.35)",
      },
    },
  },
  plugins: [],
}
