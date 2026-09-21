package com.example.fixture

import org.junit.Assert.assertEquals
import org.junit.Test

class GreetingTest {
    @Test
    fun greetingIncludesName() {
        assertEquals("Hello, Docker", Greeting.message("Docker"))
    }
}
