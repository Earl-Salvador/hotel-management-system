import java.io.*;

// ==================== 1. ABSTRACTION (Abstract Class) ====================
abstract class RoomPriceCalculator {
    protected double basePrice;
    protected int nights;
    
    public RoomPriceCalculator(double basePrice, int nights) {
        this.basePrice = basePrice;
        this.nights = nights;
    }
    
    public abstract double calculateTotal();
    
    public double getBasePrice() {
        return basePrice * nights;
    }
    
    public void displayInfo() {
        System.out.println("Base Price per night: PHP " + basePrice);
        System.out.println("Number of nights: " + nights);
    }
}

// ==================== 2. INHERITANCE ====================
class StandardRoomCalculator extends RoomPriceCalculator {
    private static final double SERVICE_FEE = 500;
    
    public StandardRoomCalculator(double basePrice, int nights) {
        super(basePrice, nights);
    }
    
    @Override
    public double calculateTotal() {
        return getBasePrice() + SERVICE_FEE;
    }
}

class DeluxeRoomCalculator extends RoomPriceCalculator {
    private static final double SERVICE_FEE = 1000;
    private static final double BREAKFAST_FEE = 350;
    
    public DeluxeRoomCalculator(double basePrice, int nights) {
        super(basePrice, nights);
    }
    
    @Override
    public double calculateTotal() {
        return getBasePrice() + SERVICE_FEE + (BREAKFAST_FEE * nights);
    }
}

class SuiteRoomCalculator extends RoomPriceCalculator {
    private static final double SERVICE_FEE = 2000;
    private static final double BREAKFAST_FEE = 500;
    private static final double SPA_FEE = 1500;
    
    public SuiteRoomCalculator(double basePrice, int nights) {
        super(basePrice, nights);
    }
    
    @Override
    public double calculateTotal() {
        return getBasePrice() + SERVICE_FEE + (BREAKFAST_FEE * nights) + (SPA_FEE * nights);
    }
}

// ==================== 3. ENCAPSULATION ====================
class Guest {
    private String name;
    private String email;
    private String phone;
    private int loyaltyPoints;
    
    public Guest(String name, String email, String phone) {
        this.name = name;
        this.email = email;
        this.phone = phone;
        this.loyaltyPoints = 0;
    }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    public int getLoyaltyPoints() { return loyaltyPoints; }
    public void addLoyaltyPoints(int points) { this.loyaltyPoints += points; }
}

// ==================== 4. POLYMORPHISM ====================
class DiscountService {
    public double applyDiscount(double amount) {
        return amount;
    }
    
    public double applyDiscount(double amount, double percent) {
        return amount * (1 - percent / 100);
    }
    
    public double applyDiscount(double amount, String couponCode) {
        if (couponCode.equals("SUMMER10")) {
            return amount * 0.90;
        } else if (couponCode.equals("WELCOME20")) {
            return amount * 0.80;
        }
        return amount;
    }
}

// ==================== MAIN CLASS ====================
public class HotelPricingCalculator {
    
    public static void main(String[] args) {
        // I-save ang output sa file
        String outputFile = "java_output.txt";
        
        try (PrintWriter writer = new PrintWriter(new FileWriter(outputFile))) {
            // Redirect System.out sa file
            PrintStream fileOut = new PrintStream(new FileOutputStream(outputFile));
            PrintStream consoleOut = System.out;
            System.setOut(fileOut);
            
            // Run the program (output goes to file)
            runProgram();
            
            System.setOut(consoleOut);
            System.out.println("Java output saved to: " + outputFile);
            
        } catch (IOException e) {
            System.err.println("Error writing to file: " + e.getMessage());
        }
    }
    
    public static void runProgram() {
        System.out.println("==========================================");
        System.out.println("    HOTEL MANAGEMENT SYSTEM - JAVA MODULE");
        System.out.println("==========================================\n");
        
        // ENCAPSULATION
        System.out.println("1. ENCAPSULATION DEMO:");
        System.out.println("----------------------");
        Guest guest = new Guest("Earl Salvador", "earl@example.com", "09123456789");
        System.out.println("Guest: " + guest.getName() + " (" + guest.getEmail() + ")");
        guest.addLoyaltyPoints(150);
        System.out.println("After adding 150 loyalty points");
        System.out.println("Total Loyalty Points: " + guest.getLoyaltyPoints());
        System.out.println();
        
        // INHERITANCE & POLYMORPHISM
        System.out.println("2. INHERITANCE & POLYMORPHISM DEMO:");
        System.out.println("-----------------------------------");
        
        int nights = 3;
        double standardPrice = 1500.00;
        double deluxePrice = 2500.00;
        double suitePrice = 4000.00;
        
        RoomPriceCalculator[] rooms = {
            new StandardRoomCalculator(standardPrice, nights),
            new DeluxeRoomCalculator(deluxePrice, nights),
            new SuiteRoomCalculator(suitePrice, nights)
        };
        
        String[] roomTypes = {"Standard Room", "Deluxe Room", "Suite"};
        
        for (int i = 0; i < rooms.length; i++) {
            System.out.println("Room Type: " + roomTypes[i]);
            System.out.println("  Base Price: PHP " + rooms[i].getBasePrice());
            System.out.println("  Total Price: PHP " + String.format("%.2f", rooms[i].calculateTotal()));
        }
        System.out.println();
        
        // POLYMORPHISM - Method Overloading
        System.out.println("3. POLYMORPHISM - METHOD OVERLOADING:");
        System.out.println("------------------------------------");
        DiscountService discountService = new DiscountService();
        double amount = 10000.00;
        
        System.out.println("Original Amount: PHP " + amount);
        System.out.println("After 10% discount: PHP " + discountService.applyDiscount(amount, 10));
        System.out.println("After SUMMER10 coupon: PHP " + discountService.applyDiscount(amount, "SUMMER10"));
        System.out.println();
        
        // ABSTRACTION
        System.out.println("4. ABSTRACTION DEMO:");
        System.out.println("--------------------");
        System.out.println("RoomPriceCalculator hides complex calculation logic.");
        System.out.println("Each room type implements its own calculateTotal() method.");
        System.out.println("\n--- 4 PILLARS OF OOP ---");
        System.out.println("1. ENCAPSULATION: Guest class with private fields");
        System.out.println("2. INHERITANCE: Room types extend RoomPriceCalculator");
        System.out.println("3. POLYMORPHISM: Method overloading and overriding");
        System.out.println("4. ABSTRACTION: Abstract class hides implementation");
    }
}