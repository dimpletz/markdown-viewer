---
name: 'Universal Coding Standards & Best Practices - All Languages'
description: 'Comprehensive coding standards and best practices for all programming languages, scripting languages, and frameworks. Ensures high-quality, secure, performant, and maintainable code.'
---

# Universal Coding Standards & Best Practices

## Core Universal Principles

### SOLID Principles (Apply to All OOP Languages)
- **Single Responsibility**: Each class/module/function has one reason to change
- **Open/Closed**: Open for extension, closed for modification  
- **Liskov Substitution**: Subtypes must be substitutable for their base types
- **Interface Segregation**: Many specific interfaces > one general interface
- **Dependency Inversion**: Depend on abstractions, not concretions

### DRY (Don't Repeat Yourself)
- Eliminate code duplication through abstraction
- Create reusable functions, classes, modules, mixins, or utilities
- Use inheritance, composition, traits, or protocols appropriately
- Centralize configuration, constants, and magic numbers

### KISS (Keep It Simple, Stupid)
- Prefer simple solutions over complex ones
- Write code that is easy to understand and maintain
- Avoid premature optimization
- Choose clarity over cleverness

### YAGNI (You Aren't Gonna Need It)
- Don't implement functionality until actually needed
- Avoid speculative generality
- Focus on current requirements, not future hypotheticals

## Universal Code Quality Standards

### Naming Conventions (Language-Agnostic Principles)
- Use descriptive, meaningful names that reveal intent
- Avoid abbreviations unless universally understood (HTTP, URL, API, ID)
- Use consistent naming patterns throughout the codebase
- Make names pronounceable and searchable
- Use domain-specific terminology
- **Booleans**: Use is/has/can/should prefix (e.g., `isValid`, `hasPermission`, `canDelete`, `shouldRetry`)
- **Functions**: Use verb or verb-noun (e.g., `calculateTotal`, `getUserById`, `validateInput`)
- **Classes**: Use nouns (e.g., `UserService`, `ProductRepository`, `PaymentProcessor`)

### Code Structure (Universal)
- **One Responsibility Per Unit**: Each function/class does one thing well
- **Function Length**: Keep functions focused (10-30 lines ideal, max 50)
- **Class Size**: Cohesive classes under 300-500 lines
- **File Organization**: One primary component per file
- **Nesting Depth**: Maximum 3-4 levels
- **Return Early**: Use guard clauses to reduce nesting
- **Cyclomatic Complexity**: Keep under 10 per function

### Comments & Documentation (Universal)
- **Self-Documenting Code**: Names should explain themselves
- **Document WHY**: Explain intent, not mechanics
- **API Documentation**: All public APIs need documentation
- **Complex Logic**: Comment non-obvious algorithms or business rules
- **TODOs**: Format as `TODO(author): description [TICKET-123]`
- **Remove Dead Code**: Delete, don't comment out
- **Keep Updated**: Remove/update outdated comments immediately

### Code Formatting (Universal)
- **Indentation**: Consistent (2 or 4 spaces, never tabs+spaces mix)
- **Line Length**: 80-120 characters maximum
- **Whitespace**: Blank lines separate logical blocks
- **Trailing Whitespace**: Remove all
- **File Endings**: Single newline at end of file
- **Auto-Formatters**: Use language-specific formatters (mandatory)

## Language-Specific Best Practices & Standards

### JavaScript / TypeScript

**Standards & Style**
- **ESLint**: Use with Airbnb or Standard style guide
- **Prettier**: Auto-format all code
- **Strict Mode**: Always use `"use strict"` or TypeScript strict
- **TypeScript**: Enable `strict`, `noImplicitAny`, `strictNullChecks`

**Modern Features (ES6+)**
```javascript
// ✅ Use const/let, never var
const maxRetries = 3;
let count = 0;

// ✅ Arrow functions for callbacks
array.map(item => item.value);

// ✅ Destructuring
const { name, email } = user;
const [first, ...rest] = array;

// ✅ Template literals
const message = `Hello, ${name}!`;

// ✅ Async/await over Promise chains
async function fetchData() {
  try {
    const response = await fetch(url);
    return await response.json();
  } catch (error) {
    logger.error('Fetch failed', error);
    throw error;
  }
}

// ✅ Optional chaining & nullish coalescing
const city = user?.address?.city ?? 'Unknown';

// ✅ Modules (ES6)
export const helper = () => {};
import { helper } from './utils';
```

**TypeScript Specific**
```typescript
// ✅ Type everything
interface User {
  id: number;
  name: string;
  email?: string;
}

function getUser(id: number): Promise<User | null> {
  // implementation
}

// ✅ Use enums for constants
enum Status {
  Active = 'ACTIVE',
  Inactive = 'INACTIVE'
}

// ✅ Generic types
function identity<T>(arg: T): T {
  return arg;
}

// ✅ Type guards
function isString(value: unknown): value is string {
  return typeof value === 'string';
}
```

**Best Practices**
- Use `===` instead of `==` (strict equality)
- Avoid global variables
- Use modules, not global scope
- Avoid `any` type in TypeScript
- Use `unknown` instead of `any` when type is uncertain
- Parse integers with radix: `parseInt(str, 10)`
- Use `Array.isArray()` to check arrays
- Prefer functional array methods: `map`, `filter`, `reduce`

---

### Python

**Standards & Style**
- **PEP 8**: Python Enhancement Proposal 8 (style guide)
- **Black**: Auto-formatter (opinionated)
- **pylint / flake8**: Linting tools
- **mypy**: Static type checker

**Best Practices**
```python
# ✅ Type hints (PEP 484)
def greet(name: str) -> str:
    return f"Hello, {name}!"

from typing import List, Dict, Optional, Union

def process_items(items: List[int]) -> Dict[str, int]:
    return {"count": len(items), "sum": sum(items)}

# ✅ Docstrings (Google or NumPy style)
def calculate_total(prices: List[float], tax_rate: float = 0.1) -> float:
    """
    Calculate total price with tax.
    
    Args:
        prices: List of item prices
        tax_rate: Tax rate as decimal (default 0.1)
        
    Returns:
        Total price including tax
        
    Raises:
        ValueError: If tax_rate is negative
    """
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")
    subtotal = sum(prices)
    return subtotal * (1 + tax_rate)

# ✅ Context managers for resources
with open('file.txt', 'r') as f:
    content = f.read()

# ✅ List comprehensions
squares = [x**2 for x in range(10) if x % 2 == 0]

# ✅ F-strings for formatting (Python 3.6+)
name = "Alice"
age = 30
message = f"{name} is {age} years old"

# ✅ Use pathlib for file paths
from pathlib import Path
config_file = Path(__file__).parent / "config.json"

# ✅ Enumerate instead of range(len())
for index, item in enumerate(items):
    print(f"{index}: {item}")

# ✅ Dictionary get with default
value = config.get('timeout', 30)

# ✅ Use dataclasses (Python 3.7+)
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
```

**Naming Conventions**
- `snake_case` for variables, functions, methods
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- `_leading_underscore` for private/internal
- `__double_leading` for name mangling

---

### PHP

**Standards & Style**
- **PSR-1**: Basic Coding Standard
- **PSR-4**: Autoloading Standard
- **PSR-12**: Extended Coding Style
- **PHP_CodeSniffer**: Enforcement tool
- **PHP-CS-Fixer**: Auto-formatter

**Modern PHP (8.0+)**
```php
<?php
// ✅ Strict types
declare(strict_types=1);

// ✅ Type declarations
function calculateTotal(float $amount, float $taxRate = 0.1): float
{
    return $amount * (1 + $taxRate);
}

// ✅ Constructor property promotion (PHP 8.0+)
class User
{
    public function __construct(
        private int $id,
        private string $name,
        private ?string $email = null
    ) {}
}

// ✅ Named arguments (PHP 8.0+)
$user = new User(id: 1, name: 'John', email: 'john@example.com');

// ✅ Match expression (PHP 8.0+)
$result = match($status) {
    'active' => 'User is active',
    'inactive' => 'User is inactive',
    default => 'Unknown status'
};

// ✅ Null coalescing operator
$username = $_GET['user'] ?? 'guest';

// ✅ Null safe operator (PHP 8.0+)
$country = $user?->getAddress()?->getCountry();

// ✅ Array destructuring
[$first, $second] = $array;

// ✅ Use statements for clarity
use App\Services\UserService;
use App\Repositories\UserRepository;
```

**Best Practices**
- Always use `<?php`, never short tags
- Use namespaces (PSR-4 autoloading)
- Type hint all parameters and return values
- Use dependency injection, never `ObjectManager` or service locators
- Validate/sanitize all inputs
- Use prepared statements for SQL (PDO/MySQLi)
- Escape output with `htmlspecialchars()`, `json_encode()`
- Use composer for dependency management
- Handle exceptions, don't suppress with `@`

---

### C# / .NET

**Standards & Style**
- **Microsoft C# Coding Conventions**
- **StyleCop / .editorconfig**: Enforcement
- **C# 10+**: Use modern features

**Best Practices**
```csharp
// ✅ Nullable reference types (C# 8.0+)
#nullable enable

public class UserService
{
    private readonly IUserRepository _repository;
    private readonly ILogger<UserService> _logger;
    
    // ✅ Constructor injection
    public UserService(
        IUserRepository repository,
        ILogger<UserService> logger)
    {
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }
    
    // ✅ Async suffix for async methods
    public async Task<User?> GetUserByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        if (id <= 0)
            throw new ArgumentException("Invalid user ID", nameof(id));
            
        try
        {
            return await _repository.GetByIdAsync(id, cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get user {UserId}", id);
            throw;
        }
    }
    
    // ✅ Expression-bodied members
    public string FullName => $"{FirstName} {LastName}";
    
    // ✅ Pattern matching (C# 9.0+)
    public string GetStatusDescription(Status status) => status switch
    {
        Status.Active => "User is active",
        Status.Inactive => "User is inactive",
        Status.Suspended => "User is suspended",
        _ => throw new ArgumentException("Invalid status", nameof(status))
    };
    
    // ✅ Record types (C# 9.0+)
    public record UserDto(int Id, string Name, string Email);
    
    // ✅ Init-only properties (C# 9.0+)
    public class User
    {
        public int Id { get; init; }
        public required string Name { get; init; }
    }
    
    // ✅ Using declarations
    using var stream = File.OpenRead("data.txt");
    
    // ✅ String interpolation
    var message = $"User {name} logged in at {DateTime.Now:yyyy-MM-dd}";
    
    // ✅ LINQ
    var activeUsers = users
        .Where(u => u.Status == Status.Active)
        .OrderBy(u => u.Name)
        .Take(10)
        .ToList();
}
```

**Naming Conventions**
- `PascalCase` for classes, methods, properties, public fields
- `camelCase` for parameters, local variables, private fields
- `_camelCase` for private fields (with underscore)
- `IPascalCase` for interfaces (I prefix)
- `TPascalCase` for type parameters

---

### Java

**Standards & Style**
- **Google Java Style Guide** or **Oracle Code Conventions**
- **Checkstyle**: Style enforcement
- **Maven/Gradle**: Build and dependency management

**Best Practices**
```java
// ✅ Package naming
package com.company.project.module;

// ✅ Imports - grouped and ordered
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

// ✅ Class structure
public class UserService {
    
    // Constants first
    private static final int MAX_RETRY_ATTEMPTS = 3;
    
    // Fields
    private final UserRepository repository;
    private final Logger logger;
    
    // Constructor
    public UserService(UserRepository repository, Logger logger) {
        this.repository = Objects.requireNonNull(repository, "repository cannot be null");
        this.logger = Objects.requireNonNull(logger, "logger cannot be null");
    }
    
    // ✅ Optional for nullable returns
    public Optional<User> findById(Long id) {
        if (id == null || id <= 0) {
            throw new IllegalArgumentException("Invalid user ID: " + id);
        }
        return repository.findById(id);
    }
    
    // ✅ Streams API (Java 8+)
    public List<String> getActiveUserNames() {
        return repository.findAll().stream()
            .filter(User::isActive)
            .map(User::getName)
            .collect(Collectors.toList());
    }
    
    // ✅ Try-with-resources
    public String readFile(String path) throws IOException {
        try (BufferedReader reader = Files.newBufferedReader(Paths.get(path))) {
            return reader.lines().collect(Collectors.joining("\n"));
        }
    }
    
    // ✅ var keyword (Java 10+)
    var users = repository.findAll();
    
    // ✅ Text blocks (Java 15+)
    String json = """
        {
            "name": "John",
            "age": 30
        }
        """;
    
    // ✅ Records (Java 14+)
    public record UserDto(Long id, String name, String email) {}
    
    // ✅ Switch expressions (Java 12+)
    String description = switch (status) {
        case ACTIVE -> "User is active";
        case INACTIVE -> "User is inactive";
        case SUSPENDED -> "User is suspended";
        default -> throw new IllegalArgumentException("Unknown status: " + status);
    };
}
```

**Naming Conventions**
- `camelCase` for variables, methods, parameters
- `PascalCase` for classes, interfaces, enums
- `UPPER_SNAKE_CASE` for constants
- Interfaces: no `I` prefix (just `UserRepository`, not `IUserRepository`)

---

### Go (Golang)

**Standards & Style**
- **Effective Go**: Official guide
- **gofmt**: Mandatory auto-formatter
- **golint / go vet**: Linting tools
- **go mod**: Dependency management

**Best Practices**
```go
package main

import (
    "context"
    "errors"
    "fmt"
    "log"
    "time"
)

// ✅ Exported names start with capital letter
type UserService struct {
    repo   UserRepository  // unexported (private)
    logger *log.Logger
}

// ✅ Constructor function
func NewUserService(repo UserRepository, logger *log.Logger) *UserService {
    if repo == nil {
        panic("repo cannot be nil")
    }
    return &UserService{
        repo:   repo,
        logger: logger,
    }
}

// ✅ Error handling (explicit)
func (s *UserService) GetUser(ctx context.Context, id int64) (*User, error) {
    if id <= 0 {
        return nil, errors.New("invalid user ID")
    }
    
    user, err := s.repo.FindByID(ctx, id)
    if err != nil {
        s.logger.Printf("failed to get user %d: %v", id, err)
        return nil, fmt.Errorf("get user: %w", err)
    }
    
    return user, nil
}

// ✅ Defer for cleanup
func (s *UserService) ProcessFile(filename string) error {
    file, err := os.Open(filename)
    if err != nil {
        return err
    }
    defer file.Close()  // Always executed
    
    // Process file...
    return nil
}

// ✅ Goroutines for concurrency
func (s *UserService) ProcessAsync(users []User) {
    for _, user := range users {
        go func(u User) {  // Capture variable
            s.process(u)
        }(user)
    }
}

// ✅ Channels for communication
func (s *UserService) ProcessWithChannel(users []User) []Result {
    results := make(chan Result, len(users))
    
    for _, user := range users {
        go func(u User) {
            results <- s.process(u)
        }(user)
    }
    
    // Collect results
    var output []Result
    for i := 0; i < len(users); i++ {
        output = append(output, <-results)
    }
    
    return output
}

// ✅ Interfaces (small and focused)
type UserRepository interface {
    FindByID(ctx context.Context, id int64) (*User, error)
    Save(ctx context.Context, user *User) error
}

// ✅ Struct embedding
type BaseService struct {
    logger *log.Logger
}

func (b *BaseService) Log(msg string) {
    b.logger.Println(msg)
}
```

**Naming Conventions**
- `camelCase` for unexported (private)
- `PascalCase` for exported (public)
- Short variable names in small scopes: `i`, `j`, `err`, `ok`
- Acronyms all caps: `HTTP`, `URL`, `ID`
- No underscores in names

---

### Ruby

**Standards & Style**
- **Ruby Style Guide** (rubocop)
- **RuboCop**: Linter and formatter
- **YARD**: Documentation

**Best Practices**
```ruby
# ✅ snake_case for methods and variables
def calculate_total(items)
  items.sum(&:price)
end

# ✅ PascalCase for classes and modules
class UserService
  attr_reader :repository
  
  def initialize(repository)
    @repository = repository
  end
  
  # ✅ Question mark for boolean methods
  def active?(user)
    user.status == 'active'
  end
  
  # ✅ Exclamation mark for dangerous methods
  def activate!(user)
    user.status = 'active'
    user.save!
  end
  
  # ✅ Blocks
  users.each do |user|
    process_user(user)
  end
  
  # ✅ Single-line blocks
  names = users.map { |u| u.name }
  
  # ✅ Symbols for hash keys
  config = { timeout: 30, retries: 3 }
  
  # ✅ String interpolation
  message = "Hello, #{user.name}!"
  
  # ✅ Guard clauses
  def process_user(user)
    return if user.nil?
    return unless user.active?
    
    # Process user...
  end
  
  # ✅ Safe navigation operator
  city = user&.address&.city
  
  # ✅ Keyword arguments
  def create_user(name:, email:, age: 18)
    # ...
  end
end

# ✅ Modules for mixins
module Timestampable
  def created_at
    @created_at ||= Time.now
  end
end

class User
  include Timestampable
end
```

---

### Rust

**Standards & Style**
- **The Rust Programming Language Book**
- **rustfmt**: Auto-formatter (mandatory)
- **clippy**: Linter

**Best Practices**
```rust
// ✅ Ownership and borrowing
fn process_string(s: String) -> String {  // Takes ownership
    s.to_uppercase()
}

fn get_length(s: &String) -> usize {  // Borrows immutably
    s.len()
}

fn append_text(s: &mut String) {  // Borrows mutably
    s.push_str(" appended");
}

// ✅ Error handling with Result
use std::fs::File;
use std::io::{self, Read};

fn read_file(path: &str) -> Result<String, io::Error> {
    let mut file = File::open(path)?;  // ? operator for early return
    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    Ok(contents)
}

// ✅ Option type for nullable values
fn find_user(id: u64) -> Option<User> {
    if id == 0 {
        None
    } else {
        Some(User::new(id))
    }
}

// ✅ Pattern matching
match result {
    Ok(value) => println!("Success: {}", value),
    Err(e) => eprintln!("Error: {}", e),
}

// ✅ If let for single pattern
if let Some(user) = find_user(123) {
    println!("Found: {}", user.name);
}

// ✅ Traits (interfaces)
trait Processable {
    fn process(&self) -> String;
}

impl Processable for User {
    fn process(&self) -> String {
        format!("Processing user: {}", self.name)
    }
}

// ✅ Lifetimes (when needed)
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// ✅ Iterators
let sum: i32 = vec![1, 2, 3, 4, 5]
    .iter()
    .filter(|&x| x % 2 == 0)
    .map(|x| x * 2)
    .sum();
```

**Naming Conventions**
- `snake_case` for variables, functions, modules
- `PascalCase` for types, traits, enums
- `SCREAMING_SNAKE_CASE` for constants
- `'lowercase` for lifetimes

---

### Swift

**Standards & Style**
- **Swift API Design Guidelines**
- **SwiftLint**: Linter
- **Swift Package Manager**: Dependencies

**Best Practices**
```swift
// ✅ Naming conventions
class UserService {
    private let repository: UserRepository
    private let logger: Logger
    
    init(repository: UserRepository, logger: Logger) {
        self.repository = repository
        self.logger = logger
    }
    
    // ✅ Optionals
    func findUser(id: Int) -> User? {
        guard id > 0 else {
            return nil
        }
        return repository.find(id: id)
    }
    
    // ✅ Guard statements
    func processUser(_ user: User?) throws {
        guard let user = user else {
            throw UserError.notFound
        }
        guard user.isActive else {
            throw UserError.inactive
        }
        // Process user...
    }
    
    // ✅ Optional binding
    if let user = findUser(id: 123) {
        print("Found: \(user.name)")
    }
    
    // ✅ Optional chaining
    let city = user?.address?.city
    
    // ✅ Nil coalescing
    let username = user?.name ?? "Guest"
    
    // ✅ Closures
    users.filter { $0.isActive }
         .map { $0.name }
         .forEach { print($0) }
    
    // ✅ Error handling
    do {
        try processUser(user)
    } catch UserError.notFound {
        print("User not found")
    } catch {
        print("Error: \(error)")
    }
    
    // ✅ Async/await (Swift 5.5+)
    func fetchUser(id: Int) async throws -> User {
        let response = try await apiClient.get("/users/\(id)")
        return try JSONDecoder().decode(User.self, from: response)
    }
}

// ✅ Protocols (interfaces)
protocol Identifiable {
    var id: Int { get }
}

// ✅ Extensions
extension String {
    var isValidEmail: Bool {
        // Email validation logic
        return true
    }
}

// ✅ Enums with associated values
enum Result<T, E> {
    case success(T)
    case failure(E)
}
```

---

### Kotlin

**Standards & Style**
- **Kotlin Coding Conventions**
- **ktlint**: Linter and formatter
- **Gradle**: Build tool

**Best Practices**
```kotlin
// ✅ Data classes
data class User(
    val id: Int,
    val name: String,
    val email: String?
)

// ✅ Nullable types
fun findUser(id: Int): User? {
    return if (id > 0) repository.findById(id) else null
}

// ✅ Null safety
val length = name?.length ?: 0  // Elvis operator

// ✅ Safe calls and let
user?.let { u ->
    println("User: ${u.name}")
}

// ✅ Extension functions
fun String.isValidEmail(): Boolean {
    return this.contains("@") && this.contains(".")
}

// ✅ When expression (switch)
val description = when (status) {
    Status.ACTIVE -> "User is active"
    Status.INACTIVE -> "User is inactive"
    else -> "Unknown"
}

// ✅ Scope functions
val user = User(1, "John", "john@example.com").apply {
    // this = user
    println("Created: $name")
}

// ✅ Collections
val activeUsers = users
    .filter { it.isActive }
    .map { it.name }
    .sorted()

// ✅ Lambdas
users.forEach { user ->
    println(user.name)
}

// ✅ Coroutines (async)
suspend fun fetchUser(id: Int): User {
    return withContext(Dispatchers.IO) {
        apiClient.getUser(id)
    }
}

// ✅ Sealed classes
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
}
```

---

### R

**Standards & Style**
- **tidyverse style guide**
- **lintr**: Linting package
- **styler**: Auto-formatter

**Best Practices**
```r
# ✅ snake_case for functions and variables
calculate_mean <- function(values) {
  sum(values) / length(values)
}

# ✅ Use <- for assignment (not =)
total <- sum(prices)

# ✅ Vectorization (avoid loops when possible)
# Bad
total <- 0
for (i in 1:length(values)) {
  total <- total + values[i]
}

# Good
total <- sum(values)

# ✅ Pipes (magrittr or native |>)
library(dplyr)

result <- data %>%
  filter(age > 18) %>%
  select(name, email) %>%
  arrange(name)

# ✅ tidyverse functions
library(tidyverse)

users <- read_csv("users.csv") %>%
  mutate(age_group = case_when(
    age < 18 ~ "minor",
    age < 65 ~ "adult",
    TRUE ~ "senior"
  )) %>%
  group_by(age_group) %>%
  summarise(count = n(), avg_age = mean(age))

# ✅ Functions with default arguments
process_data <- function(data, method = "mean", na.rm = TRUE) {
  if (method == "mean") {
    mean(data, na.rm = na.rm)
  } else {
    median(data, na.rm = na.rm)
  }
}

# ✅ Error handling
tryCatch({
  result <- risky_operation()
}, error = function(e) {
  message("Error occurred: ", e$message)
  return(NULL)
})
```

---

### Shell Scripting (Bash)

**Standards & Style**
- **Google Shell Style Guide**
- **ShellCheck**: Linter

**Best Practices**
```bash
#!/usr/bin/env bash

# ✅ Strict mode
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ✅ Constants in UPPER_CASE
readonly MAX_RETRIES=3
readonly LOG_FILE="/var/log/script.log"

# ✅ Functions in lowercase
log_message() {
  local message="$1"
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] ${message}" >> "${LOG_FILE}"
}

# ✅ Quote variables
name="John Doe"
echo "Hello, ${name}"

# ✅ Use [[ ]] for conditionals
if [[ -f "${file}" ]]; then
  echo "File exists"
fi

# ✅ Parameter expansion with defaults
username="${1:-defaultuser}"
port="${PORT:-8080}"

# ✅ Arrays
files=("file1.txt" "file2.txt" "file3.txt")
for file in "${files[@]}"; do
  process_file "${file}"
done

# ✅ Command substitution with $()
current_date=$(date +%Y-%m-%d)
file_count=$(ls -1 | wc -l)

# ✅ Check command success
if command -v docker &> /dev/null; then
  echo "Docker is installed"
fi

# ✅ Here documents
cat <<EOF > config.txt
server=${SERVER}
port=${PORT}
EOF

# ✅ Error handling
process_file() {
  local file="$1"
  
  if [[ ! -f "${file}" ]]; then
    echo "Error: File not found: ${file}" >&2
    return 1
  fi
  
  # Process file...
  return 0
}

# ✅ Use local variables in functions
calculate_sum() {
  local num1="$1"
  local num2="$2"
  echo $((num1 + num2))
}

# ✅ Exit codes
main() {
  # Main logic
  return 0
}

main "$@"
exit $?
```

---

### PowerShell

**Standards & Style**
- **PowerShell Best Practices and Style Guide**
- **PSScriptAnalyzer**: Linter

**Best Practices**
```powershell
# ✅ Use approved verbs (Get, Set, New, Remove, etc.)
function Get-UserData {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [int]$UserId,
        
        [Parameter(Mandatory=$false)]
        [string]$Format = "json"
    )
    
    # ✅ Use Write-Verbose for detailed logging
    Write-Verbose "Fetching user data for ID: $UserId"
    
    # ✅ Try-catch for error handling
    try {
        $user = Get-User -Id $UserId -ErrorAction Stop
        
        switch ($Format) {
            "json" { $user | ConvertTo-Json }
            "xml"  { $user | ConvertTo-Xml }
            default { $user }
        }
    }
    catch {
        Write-Error "Failed to get user: $_"
        throw
    }
}

# ✅ Use PascalCase for function names
function New-Configuration {
    param([string]$Path)
    # Implementation
}

# ✅ Splatting for parameters
$params = @{
    Path        = "C:\Files"
    Filter      = "*.txt"
    Recurse     = $true
    ErrorAction = "Stop"
}
Get-ChildItem @params

# ✅ Pipeline and ForEach-Object
Get-ChildItem -Path "C:\Logs" -Filter "*.log" |
    Where-Object { $_.Length -gt 1MB } |
    ForEach-Object {
        Write-Host "Large file: $($_.Name)"
    }

# ✅ Use [PSCustomObject] for objects
$user = [PSCustomObject]@{
    Id    = 1
    Name  = "John"
    Email = "john@example.com"
}

# ✅ Parameter validation
function Set-Configuration {
    param(
        [ValidateNotNullOrEmpty()]
        [string]$Name,
        
        [ValidateRange(1, 100)]
        [int]$Value
    )
}

# ✅ Advanced function with common parameters
function Invoke-Process {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$Name)
    
    if ($PSCmdlet.ShouldProcess($Name, "Process")) {
        # Perform action
    }
}
```

---

### SQL (All Variants)

**Standards & Style**
- **SQL Style Guide** (various)
- **Keywords in UPPERCASE, identifiers in lowercase**

**Best Practices**
```sql
-- ✅ Keywords in UPPERCASE
SELECT 
    u.id,
    u.name,
    u.email,
    COUNT(o.id) AS order_count
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
    AND u.created_at >= '2024-01-01'
GROUP BY u.id, u.name, u.email
HAVING COUNT(o.id) > 5
ORDER BY order_count DESC
LIMIT 100;

-- ✅ Use meaningful aliases
SELECT 
    u.name AS user_name,
    o.total AS order_total
FROM users u
JOIN orders o ON u.id = o.user_id;

-- ✅ Parameterized queries (prevent SQL injection)
-- Application code:
-- query = "SELECT * FROM users WHERE email = ?"
-- execute(query, [user_email])

-- ✅ Indexes for frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at);

-- ✅ Use transactions for data integrity
BEGIN TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

COMMIT;

-- ✅ Common Table Expressions (CTEs) for readability
WITH active_users AS (
    SELECT id, name, email
    FROM users
    WHERE status = 'active'
),
user_orders AS (
    SELECT 
        user_id,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY user_id
)
SELECT 
    u.name,
    u.email,
    COALESCE(uo.order_count, 0) AS orders
FROM active_users u
LEFT JOIN user_orders uo ON u.id = uo.user_id;

-- ✅ Avoid SELECT * (specify columns)
SELECT id, name, email FROM users;  -- Good
SELECT * FROM users;                -- Avoid

-- ✅ Use EXISTS instead of IN for subqueries (better performance)
SELECT name FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id
);
```

---

### HTML

**Standards & Style**
- **W3C HTML Standards**
- **Semantic HTML5**
- **Accessibility (WCAG 2.1 AA)**

**Best Practices**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Page description for SEO">
    <title>Page Title - Site Name</title>
</head>
<body>
    <!-- ✅ Use semantic elements -->
    <header>
        <nav aria-label="Main navigation">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <!-- ✅ Proper heading hierarchy -->
        <h1>Main Page Heading</h1>
        
        <article>
            <h2>Article Title</h2>
            <p>Article content...</p>
        </article>
        
        <!-- ✅ Accessible forms -->
        <form action="/submit" method="POST">
            <label for="username">Username:</label>
            <input 
                type="text" 
                id="username" 
                name="username" 
                required 
                aria-describedby="username-help">
            <small id="username-help">Enter your username</small>
            
            <button type="submit">Submit</button>
        </form>
        
        <!-- ✅ Alt text for images -->
        <img src="logo.png" alt="Company Logo">
        
        <!-- ✅ ARIA labels when needed -->
        <button aria-label="Close dialog">
            <span aria-hidden="true">&times;</span>
        </button>
    </main>
    
    <footer>
        <p>&copy; 2026 Company Name</p>
    </footer>
</body>
</html>
```

---

### CSS / SCSS

**Standards & Style**
- **BEM (Block Element Modifier)** or similar methodology
- **CSS Lint / Stylelint**
- **Modern CSS features**

**Best Practices**
```css
/* ✅ Use BEM naming convention */
.card {
    display: flex;
    padding: 1rem;
    border-radius: 0.5rem;
}

.card__title {
    font-size: 1.5rem;
    font-weight: bold;
}

.card__content {
    color: #333;
}

.card--featured {
    background-color: #f0f0f0;
}

/* ✅ CSS Custom Properties (variables) */
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --spacing-unit: 0.5rem;
    --font-family-base: 'Arial', sans-serif;
}

.button {
    background-color: var(--primary-color);
    padding: calc(var(--spacing-unit) * 2);
    font-family: var(--font-family-base);
}

/* ✅ Mobile-first responsive design */
.container {
    width: 100%;
    padding: 1rem;
}

@media (min-width: 768px) {
    .container {
        max-width: 720px;
        margin: 0 auto;
    }
}

@media (min-width: 1024px) {
    .container {
        max-width: 960px;
    }
}

/* ✅ Flexbox and Grid */
.layout {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
}

.flex-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* ✅ Avoid !important (use specificity correctly) */
/* Bad */
.text { color: red !important; }

/* Good */
.section .text { color: red; }

/* ✅ Use shorthand properties */
/* Bad */
margin-top: 1rem;
margin-right: 1rem;
margin-bottom: 1rem;
margin-left: 1rem;

/* Good */
margin: 1rem;

/* ✅ Group related properties */
.element {
    /* Positioning */
    position: relative;
    top: 0;
    left: 0;
    
    /* Display & Box Model */
    display: block;
    width: 100%;
    padding: 1rem;
    margin: 0;
    
    /* Typography */
    font-size: 1rem;
    line-height: 1.5;
    color: #333;
    
    /* Visual */
    background-color: #fff;
    border: 1px solid #ddd;
    border-radius: 0.25rem;
    
    /* Misc */
    cursor: pointer;
}
```

---

### YAML

**Standards & Style**
- **Consistent indentation (2 spaces)**
- **yamllint**: Linting tool

**Best Practices**
```yaml
# ✅ Use 2-space indentation
apiVersion: v1
kind: Service
metadata:
  name: my-service
  labels:
    app: my-app
    environment: production

# ✅ Use quotes for strings with special characters
description: "This is a description: with special chars"

# ✅ Multi-line strings
script: |
  #!/bin/bash
  echo "Line 1"
  echo "Line 2"

# ✅ Use anchors and aliases for reusability
defaults: &defaults
  timeout: 30
  retries: 3

service_a:
  <<: *defaults
  name: service-a

service_b:
  <<: *defaults
  name: service-b
  retries: 5  # Override

# ✅ Comments
# This is a comment explaining the configuration
max_connections: 100  # Inline comment

# ✅ Arrays
services:
  - web
  - api
  - worker

# Or inline
services: [web, api, worker]

# ✅ Boolean values
enabled: true
debug: false
```

---

### JSON

**Standards & Style**
- **RFC 8259: JSON Standard**
- **jq / prettier**: Formatting tools

**Best Practices**
```json
{
  "name": "project-name",
  "version": "1.0.0",
  "description": "Project description",
  "config": {
    "timeout": 30,
    "retries": 3,
    "enabled": true,
    "threshold": 0.95
  },
  "items": [
    {
      "id": 1,
      "name": "Item 1",
      "active": true
    },
    {
      "id": 2,
      "name": "Item 2",
      "active": false
    }
  ],
  "metadata": {
    "created": "2026-03-17T10:00:00Z",
    "author": "John Doe"
  }
}
```

**Rules**
- Use double quotes for strings
- No trailing commas
- No comments (use JSON5 or JSONC if comments needed)
- Use 2 or 4 space indentation consistently
- Property names in camelCase or snake_case (be consistent)

---

## Universal Security Best Practices

### Input Validation & Sanitization
```
✅ Validate ALL inputs
✅ Whitelist over blacklist
✅ Type checking and length limits
✅ Format validation (regex for email, URL, phone, etc.)
✅ Sanitize based on output context (HTML, SQL, JS, URL)
```

### OWASP Top 10 Protection

**1. SQL Injection**
```sql
-- ❌ BAD: String concatenation
query = "SELECT * FROM users WHERE email = '" + userInput + "'";

-- ✅ GOOD: Parameterized queries
query = "SELECT * FROM users WHERE email = ?";
execute(query, [userInput]);
```

**2. XSS (Cross-Site Scripting)**
```javascript
// ❌ BAD: Direct insertion
element.innerHTML = userInput;

// ✅ GOOD: Escape or use textContent
element.textContent = userInput;
// Or use DOMPurify library
element.innerHTML = DOMPurify.sanitize(userInput);
```

**3. CSRF (Cross-Site Request Forgery)**
```javascript
// ✅ Use anti-CSRF tokens in all state-changing operations
<form method="post">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <!-- form fields -->
</form>
```

**4. Authentication & Authorization**
```
✅ Strong password policies (min length, complexity)
✅ Multi-factor authentication (MFA)
✅ Secure session management
✅ Check authorization on EVERY protected resource
✅ Principle of least privilege
```

**5. Sensitive Data Exposure**
```
✅ Encrypt data at rest (AES-256)
✅ Encrypt data in transit (TLS 1.2+)
✅ Never log sensitive data (passwords, tokens, PII)
✅ Use HTTPS everywhere
✅ Secure cookies (HttpOnly, Secure, SameSite)
```

**6. Security Misconfiguration**
```
✅ Disable debug mode in production
✅ Remove default credentials
✅ Set security headers (CSP, X-Frame-Options, etc.)
✅ Keep software updated
✅ Minimal permissions
```

### Secrets Management
```
❌ Never hardcode secrets
✅ Use environment variables
✅ Use secret management systems (Vault, AWS Secrets Manager, Azure Key Vault)
✅ Rotate secrets regularly
✅ Use .gitignore for sensitive files
✅ Scan git history for leaked secrets
```

---

## Universal Performance Best Practices

### Database Optimization
```
✅ Use indexes on frequently queried columns
✅ Avoid N+1 queries (use eager loading/joins)
✅ Use connection pooling
✅ Implement pagination
✅ Cache frequently accessed data
✅ Use EXPLAIN to analyze query plans
✅ Batch operations instead of loops
✅ Keep transactions short
```

### Caching Strategies
```
✅ Cache at multiple levels (browser, CDN, application, database)
✅ Set appropriate TTL (Time-To-Live)
✅ Implement cache invalidation
✅ Use consistent cache keys
✅ Cache immutable data aggressively
✅ Use Redis/Memcached for distributed caching
```

### Code Optimization
```
✅ Profile before optimizing
✅ Optimize algorithms (O(n) > O(n²))
✅ Lazy loading for expensive operations
✅ Async/await for I/O operations
✅ Use streaming for large datasets
✅ Minimize memory allocations
✅ Object pooling for expensive objects
```

---

## Universal Testing Best Practices

### Test Coverage Requirements
```
✅ Minimum 80% line coverage
✅ Minimum 80% branch coverage
✅ 100% coverage for critical business logic
✅ Test all public APIs
```

### Test Types & Pyramid
```
       /\
      /E2E\        Few (slow, expensive, brittle)
     /------\
    /  Integ  \    Some (moderate speed, setup required)
   /-----------\
  /    Unit     \  Many (fast, isolated, reliable)
 /---------------\
```

### Test Structure (Universal AAA Pattern)
```
Arrange - Set up test data and dependencies
Act     - Execute the code under test
Assert  - Verify the outcome
```

### What to Test
```
✅ Happy path (valid inputs, expected results)
✅ Error cases (invalid inputs, exceptions)
✅ Edge cases (null, empty, max/min values,boundaries)
✅ Security (injection, unauthorized access)
✅ Performance (for critical paths)
✅ Integration points (external services, databases)
```

### Test Quality Rules
```
✅ Tests must be independent (no shared state)
✅ Tests must be repeatable (same result every time)
✅ Tests must be fast (unit tests in milliseconds)
✅ Tests must be readable (clear intent)
✅ One logical assertion per test (or related assertions)
✅ Mock all external dependencies in unit tests
✅ No logic in tests (keep them simple)
```

---

## Version Control Best Practices

### Git Commit Messages
```
Format:
<type>(<scope>): <subject>

<body>

<footer>

Types: feat, fix, docs, style, refactor, test, chore, perf
Example:
feat(auth): add JWT token refresh mechanism

Implement automatic token refresh when token expires.
Uses refresh token stored in httpOnly cookie.

Closes #123
```

### Branch Naming
```
feature/user-authentication
bugfix/fix-login-error
hotfix/security-patch
release/v1.2.0
chore/update-dependencies
```

### Git Workflow Rules
```
✅ Commit often, small logical changes
✅ Never commit secrets or sensitive data
✅ Write meaningful commit messages
✅ Keep branches short-lived
✅ Rebase to keep history clean (when appropriate)
✅ Review your own code before PR
✅ Request code review before merging
✅ Run tests before committing
✅ Use .gitignore properly
```

---

## Documentation Standards

### Code Documentation
```
✅ README for every project
✅ API documentation for all public APIs
✅ Architecture diagrams (use Mermaid)
✅ Setup/installation instructions
✅ Configuration guide
✅ Deployment guide
✅ Troubleshooting section
✅ Contributing guidelines
```

### Comment Quality
```
✅ Explain WHY, not WHAT
✅ Document complex algorithms
✅ Document non-obvious decisions
✅ Update comments when code changes
✅ Remove obsolete comments
✅ Use TODO with context and ticket number
```

---

## Accessibility (A11y)

### WCAG 2.1 Level AA Standards
```
✅ Semantic HTML (proper elements)
✅ Keyboard navigation (all interactive elements)
✅ Screen reader support (ARIA labels)
✅ Color contrast 4.5:1 for text
✅ Alt text for images
✅ Focus indicators
✅ Skip navigation links
✅ Form labels
✅ Error messages associated with fields
```

---

## Monitoring & Logging

### Logging Best Practices
```
✅ Use structured logging (JSON format)
✅ Log levels: DEBUG, INFO, WARN, ERROR, FATAL
✅ Include context (user ID, request ID, timestamp)
✅ Use correlation IDs for distributed systems
✅ Never log sensitive data (passwords, tokens, SSN, credit cards)
✅ Log errors with stack traces
✅ Log performance metrics (slow queries, API response times)
✅ Use centralized logging (ELK, Splunk, CloudWatch)
```

### What to Log
```
✅ Application lifecycle events (start, stop, restart)
✅ Errors and exceptions (with full context)
✅ Security events (login, logout, permission changes, failed auth)
✅ Business-critical operations
✅ External API calls (request/response without secrets)
✅ Database slow queries
✅ Performance metrics
```

---

## Final Development Checklist

Before considering code complete:

**Code Quality**
- [ ] Follows language-specific conventions
- [ ] SOLID principles applied
- [ ] No code duplication (DRY)
- [ ] Functions are small and focused
- [ ] Names are clear and descriptive
- [ ] No magic numbers (use constants)
- [ ] Proper error handling
- [ ] No dead code or commented-out code

**Security**
- [ ] All inputs validated and sanitized
- [ ] No SQL injection vulnerabilities (parameterized queries)
- [ ] XSS protection (proper output escaping)
- [ ] CSRF protection implemented
- [ ] No hardcoded secrets
- [ ] Authentication/authorization checked
- [ ] Secure communication (HTTPS)

**Performance**
- [ ] No N+1 query problems
- [ ] Proper indexing on database queries
- [ ] Caching implemented where appropriate
- [ ] Async operations for I/O-bound tasks
- [ ] No memory leaks
- [ ] Resources properly disposed

**Testing**
- [ ] Unit tests written and passing
- [ ] Minimum 80% code coverage
- [ ] Edge cases tested
- [ ] Error scenarios tested
- [ ] Integration tests (if applicable)
- [ ] All tests are independent and repeatable

**Documentation**
- [ ] Code comments for complex logic
- [ ] API documentation updated
- [ ] README updated (if needed)
- [ ] CHANGELOG updated
- [ ] Architecture diagrams current (Mermaid)

**Version Control**
- [ ] Clear, descriptive commit messages
- [ ] Small, logical commits
- [ ] No sensitive data committed
- [ ] Self-reviewed before PR
- [ ] Ready for peer review

**Accessibility**
- [ ] Semantic HTML used
- [ ] Keyboard navigation works
- [ ] Screen reader tested
- [ ] Color contrast sufficient
- [ ] Alt text for images

**Final Checks**
- [ ] Runs locally without errors
- [ ] No console warnings/errors
- [ ] Linter passing
- [ ] Formatted with auto-formatter
- [ ] All TODOs resolved or documented
- [ ] Deployment documentation updated

---

**Remember**: 
- **Code is read 10x more than written** - optimize for readability
- **Security is not optional** - validate, sanitize, encrypt
- **Test your code** - untested code is broken code
- **Document decisions** - future you will thank present you
- **Keep learning** - languages and frameworks evolve
- **Ask for reviews** - fresh eyes catch issues
- **Automate everything** - formatting, linting, testing, deployment

---

*This instruction file applies universally to all code. Follow language-specific conventions where they exist, and general principles everywhere else.*
