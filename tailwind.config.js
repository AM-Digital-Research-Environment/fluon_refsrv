/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/fo_services/templates/**/*.html"],
  theme: {
    fontFamily: {
      mono: ["Inconsolata", "ui-monospace"],
    },
    extend: {},
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};
