import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#1565c0" },
    secondary: { main: "#00838f" },
    background: { default: "#f4f6f8" },
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: ['"Inter"', "Roboto", "Helvetica", "Arial", "sans-serif"].join(","),
  },
});
