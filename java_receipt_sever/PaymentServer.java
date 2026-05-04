import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import java.util.stream.Collectors;

public class PaymentServer {
    public static void main(String[] args) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/calculate-tax", new TaxHandler());
        server.createContext("/process-payment", new PaymentHandler());
        server.setExecutor(null);
        server.start();
        System.out.println("Payment & Tax server started on port 8080");
    }

    // Tax Calculation Handler
    static class TaxHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if ("POST".equals(exchange.getRequestMethod())) {
                // Read request body
                String body = new BufferedReader(
                    new InputStreamReader(exchange.getRequestBody(), StandardCharsets.UTF_8))
                    .lines()
                    .collect(Collectors.joining("\n"));
                
                // Parse simple JSON manually (no external libs)
                double amount = extractDouble(body, "amount");
                double taxRate = extractDouble(body, "taxRate");
                if (taxRate <= 0) taxRate = 12.0;
                
                double taxAmount = amount * (taxRate / 100);
                double totalWithTax = amount + taxAmount;
                
                // Build JSON response manually
                String response = String.format(
                    "{\"originalAmount\":%.2f,\"taxRate\":%.2f,\"taxAmount\":%.2f,\"totalAmount\":%.2f,\"currency\":\"PHP\"}",
                    amount, taxRate, taxAmount, totalWithTax);
                
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.getBytes().length);
                OutputStream os = exchange.getResponseBody();
                os.write(response.getBytes());
                os.close();
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
        }
    }

    // Payment Processing Handler
    static class PaymentHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if ("POST".equals(exchange.getRequestMethod())) {
                // Read request body
                String body = new BufferedReader(
                    new InputStreamReader(exchange.getRequestBody(), StandardCharsets.UTF_8))
                    .lines()
                    .collect(Collectors.joining("\n"));
                
                // Parse JSON manually
                double amount = extractDouble(body, "amount");
                String paymentMethod = extractString(body, "paymentMethod");
                String bookingId = extractString(body, "bookingId");
                
                // Generate transaction ID
                String transactionId = "TXN-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
                boolean paymentSuccess = true;
                
                // Build JSON response
                String response = String.format(
                    "{\"success\":%b,\"transactionId\":\"%s\",\"amount\":%.2f,\"paymentMethod\":\"%s\",\"status\":\"%s\",\"message\":\"%s\"}",
                    paymentSuccess, transactionId, amount, paymentMethod, "completed", "Payment processed successfully");
                
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.getBytes().length);
                OutputStream os = exchange.getResponseBody();
                os.write(response.getBytes());
                os.close();
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
        }
    }
    
    // Helper method to extract double from JSON string
    private static double extractDouble(String json, String key) {
        String search = "\"" + key + "\":";
        int start = json.indexOf(search);
        if (start == -1) return 0;
        start += search.length();
        int end = json.indexOf(",", start);
        if (end == -1) end = json.indexOf("}", start);
        if (end == -1) end = json.length();
        try {
            return Double.parseDouble(json.substring(start, end).trim());
        } catch (NumberFormatException e) {
            return 0;
        }
    }
    
    // Helper method to extract string from JSON
    private static String extractString(String json, String key) {
        String search = "\"" + key + "\":\"";
        int start = json.indexOf(search);
        if (start == -1) return "";
        start += search.length();
        int end = json.indexOf("\"", start);
        if (end == -1) return "";
        return json.substring(start, end);
    }
}