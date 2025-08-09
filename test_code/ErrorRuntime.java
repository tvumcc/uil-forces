import java.util.*;
import java.io.*;

public class ErrorRuntime {
    public static void main(String[] args) throws IOException {
        Scanner in = new Scanner(new File("thomas.dat"));

        for (int i = 0; i < 10; i++) {
            System.out.println(in.next());
        }
    }
}